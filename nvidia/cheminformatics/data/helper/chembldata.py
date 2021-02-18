import warnings
warnings.filterwarnings("ignore", message=r"deprecated", category=FutureWarning)

import cudf
import pandas
import sqlite3
import logging

from dask import delayed, dataframe

from contextlib import closing
from nvidia.cheminformatics.utils.singleton import Singleton
from nvidia.cheminformatics.smiles import RemoveSalt, PreprocessSmiles
from nvidia.cheminformatics.fingerprint import MorganFingerprint
from nvidia.cheminformatics.config import Context

SMILES_TRANSFORMS = [RemoveSalt(), PreprocessSmiles()]

SQL_MOLECULAR_PROP = """
SELECT md.molregno as molregno, md.chembl_id, cp.*, cs.*
FROM compound_properties cp,
        compound_structures cs,
        molecule_dictionary md
WHERE cp.molregno = md.molregno
        AND md.molregno = cs.molregno
        AND md.molregno in (%s)
"""


logger = logging.getLogger(__name__)


IMP_PROPS = [
    'alogp',
    'aromatic_rings',
    'full_mwt',
    'psa',
    'rtb']
ADDITIONAL_FEILD = ['canonical_smiles', 'transformed_smiles']

IMP_PROPS_TYPE = [pandas.Series([], dtype='float64'),
                  pandas.Series([], dtype='int64'),
                  pandas.Series([], dtype='float64'),
                  pandas.Series([], dtype='float64'),
                  pandas.Series([], dtype='int64')]
ADDITIONAL_FEILD_TYPE = [pandas.Series([], dtype='object'),
                         pandas.Series([], dtype='object')]


# DEPRECATED. Please add code to DAO classes.
class ChEmblData(object, metaclass=Singleton):

    def __init__(self,
                 fp_type=MorganFingerprint):

        context = Context()
        db_file = context.get_config('data_mount_path', default='/data')

        self.chembl_db = 'file:%s/db/chembl_27.db?mode=ro' % db_file
        self.fp_type = fp_type

        logger.info('Reading ChEMBL database at %s...' % self.chembl_db)

    def fetch_props_by_molregno(self, molregnos):
        """
        Returns compound properties and structure filtered by ChEMBL IDs along
        with a list of columns.
        """
        with closing(sqlite3.connect(self.chembl_db, uri=True)) as con, con,  \
                closing(con.cursor()) as cur:
            select_stmt = SQL_MOLECULAR_PROP % " ,".join(list(map(str, molregnos)))
            cur.execute(select_stmt)

            cols = list(map(lambda x: x[0], cur.description))
            return cols, cur.fetchall()

    def fetch_props_df_by_molregno(self, molregnos, gpu=True):
        """
        Returns compound properties and structure filtered by ChEMBL IDs in a
        dataframe.
        """
        select_stmt = SQL_MOLECULAR_PROP % " ,".join(molregnos)
        df = pandas.read_sql(select_stmt,
                             sqlite3.connect(self.chembl_db, uri=True),
                             index_col='molregno')
        if gpu:
            return cudf.from_pandas(df)
        else:
            return df

    def fetch_molregno_by_chemblId(self, chemblIds):
        logger.debug('Fetch ChEMBL ID using molregno...')
        with closing(sqlite3.connect(self.chembl_db, uri=True)) as con, con,  \
                closing(con.cursor()) as cur:
            select_stmt = '''
                SELECT md.molregno as molregno
                FROM compound_properties cp,
                        compound_structures cs,
                        molecule_dictionary md
                WHERE cp.molregno = md.molregno
                    AND md.molregno = cs.molregno
                    AND md.chembl_id in (%s)
            ''' %  "'%s'" %"','".join(chemblIds)
            cur.execute(select_stmt)
            return cur.fetchall()


    def fetch_chemblId_by_molregno(self, molregnos):
        logger.debug('Fetch ChEMBL ID using molregno...')
        with closing(sqlite3.connect(self.chembl_db, uri=True)) as con, con,  \
                closing(con.cursor()) as cur:
            select_stmt = '''
                SELECT md.chembl_id as chembl_id
                FROM molecule_dictionary md
                WHERE md.molregno in (%s)
            ''' %  ", ".join(list(map(str, molregnos)))
            cur.execute(select_stmt)
            return cur.fetchall()

    def fetch_molecule_cnt(self):
        logger.debug('Finding number of molecules...')
        with closing(sqlite3.connect(self.chembl_db, uri=True)) as con, con,  \
                closing(con.cursor()) as cur:
            select_stmt = '''
                SELECT count(*)
                FROM compound_properties cp,
                     molecule_dictionary md,
                     compound_structures cs
                WHERE cp.molregno = md.molregno
                      AND md.molregno = cs.molregno
            '''
            cur.execute(select_stmt)

            return cur.fetchone()[0]

    def _meta_df(self, **transformation_kwargs):
        transformation = self.fp_type(**transformation_kwargs)

        prop_meta = {'id': pandas.Series([], dtype='int64')}
        prop_meta.update(dict(zip(IMP_PROPS + ADDITIONAL_FEILD,
                              IMP_PROPS_TYPE + ADDITIONAL_FEILD_TYPE)))
        prop_meta.update({i: pandas.Series([], dtype='float32') for i in range(len(transformation))})

        return pandas.DataFrame(prop_meta)

    def _fetch_mol_embedding(self,
                             start=0,
                             batch_size=5000,
                             smiles_transforms=SMILES_TRANSFORMS,
                             molregnos=None,
                             **transformation_kwargs):
        """
        Returns compound properties and structure for the first N number of
        records in a dataframe.
        """

        logger.info('Fetching %d records starting %d...' % (batch_size, start))

        imp_cols = [ 'cp.' + col for col in IMP_PROPS]

        if molregnos is None:
            select_stmt = '''
                SELECT md.molregno, %s, cs.canonical_smiles
                FROM compound_properties cp,
                    molecule_dictionary md,
                    compound_structures cs
                WHERE cp.molregno = md.molregno
                    AND md.molregno = cs.molregno
                LIMIT %d, %d
            ''' % (', '.join(imp_cols), start, batch_size)
        else:
            select_stmt = '''
                SELECT md.molregno, %s, cs.canonical_smiles
                FROM compound_properties cp,
                    molecule_dictionary md,
                    compound_structures cs
                WHERE cp.molregno = md.molregno
                    AND md.molregno = cs.molregno
                    AND md.molregno in (%s)
                LIMIT %d, %d
            ''' % (', '.join(imp_cols), " ,".join(list(map(str, molregnos))), start, batch_size)

        df = pandas.read_sql(select_stmt,
                            sqlite3.connect(self.chembl_db, uri=True))

        # Smiles -> Smiles transformation and filtering
        df['transformed_smiles'] = df['canonical_smiles']
        if smiles_transforms is not None:
            if len(smiles_transforms) > 0:
                for xf in smiles_transforms:
                    df['transformed_smiles'] = df['transformed_smiles'].map(xf.transform)
                    df.dropna(subset=['transformed_smiles'], axis=0, inplace=True)

        # Conversion to fingerprints or embeddings
        transformation = self.fp_type(**transformation_kwargs)
        return_df = df.apply(transformation.transform, result_type='expand', axis=1)

        return_df = pandas.DataFrame(
            return_df,
            columns=pandas.RangeIndex(start=0,
                                      stop=len(transformation))).astype('float32')

        return_df = df.merge(return_df, left_index=True, right_index=True)
        return_df.rename(columns={'molregno': 'id'}, inplace=True)
        return return_df

    def fetch_mol_embedding(self,
                            num_recs=None,
                            batch_size=5000,
                            molregnos=None,
                            **transformation_kwargs):
        """
        Returns compound properties and structure for the first N number of
        records in a dataframe.
        """
        logger.debug('Fetching properties for all molecules...')

        if not num_recs or num_recs < 0:
            num_recs = self.fetch_molecule_cnt()

        meta_df = self._meta_df(**transformation_kwargs)

        dls = []
        for start in range(0, num_recs, batch_size):
            bsize = min(num_recs - start, batch_size)
            dl_data = delayed(self._fetch_mol_embedding) \
                             (start=start, batch_size=bsize, molregnos=molregnos, **transformation_kwargs)
            dls.append(dl_data)

        return dataframe.from_delayed(dls, meta=meta_df)

    def save_fingerprints(self, hdf_path='data/filter_*.h5', num_recs=None):
        """
        Generates fingerprints for all ChEMBL ID's in the database
        """
        logger.debug('Fetching molecules from database for fingerprints...')

        mol_df = self.fetch_mol_embedding(num_recs=num_recs)
        mol_df.to_hdf(hdf_path, 'fingerprints')