import logging
import numba
from numba.types import bool_, string, int64

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit import DataStructs


logger = logging.getLogger(__name__)


@numba.jit(bool_[:, :](string[:], int64, int64), forceobj=True, parallel=True)
def calculate_morgan_fingerprint(smiles, radius, nbits):
    '''
    Calculate Morgan fingerprint for a series of SMILES strings.

    Parameters
    ----------
    smiles : array_like
        The array of SMILES strings to be processed.
    radius : int
        The radius of the Morgan fingerprint.
    nbits : int
        The number of bits in the Morgan fingerprint.
    '''
    fingerprints = np.empty((smiles.shape[0], nbits), dtype=np.bool_)
    for i in range(smiles.shape[0]):
        mol = Chem.MolFromSmiles(smiles[i])
        if mol:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nbits)
            fp = np.fromstring(fp.ToBitString(), 'u1') - ord('0')
        else:
            fp = np.zeros(nbits, dtype=bool)

        fingerprints[i] = fp
    return fingerprints

def calc_morgan_fingerprints(dataframe, smiles_col='canonical_smiles', remove_invalid=True, nbits = 512):
    """Calculate Morgan fingerprints on SMILES strings

    Args:
        dataframe (pandas/cudf.DataFrame): dataframe containing a SMILES column for calculation
        remove_invalid (bool): remove fingerprints from failed SMILES conversion, default: True

    Returns:
        pandas/cudf.DataFrame: new dataframe containing fingerprints
    """
    fp = calculate_morgan_fingerprint(dataframe[smiles_col].values, 2, nbits)
    fp = pd.DataFrame(fp, index=dataframe.index)

    # Check for invalid smiles
    # Prune molecules which failed to convert or throw error and exit
    valid_molecule_mask = (fp.sum(axis=1) > 0)
    num_invalid_molecules = int(valid_molecule_mask.shape[0] - valid_molecule_mask.sum())
    if num_invalid_molecules > 0:
        logger.warn(f'WARNING: Found {num_invalid_molecules} invalid fingerprints due to invalid SMILES during fingerprint creation')
        if remove_invalid:
            logger.info(f'Removing {num_invalid_molecules} invalid fingerprints due to invalid SMILES during fingerprint creation')
            fp = fp[valid_molecule_mask]

    return fp

def get_murcko_scaffold(smiles: str):
    if smiles is None:
        return 'NONE'
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 'NONE'
    scaff =  MurckoScaffold.MurckoScaffoldSmilesFromSmiles(smiles)
    if scaff == '':
        return 'NONE'
    return scaff

def calc_fingerprint(smiles, radius = 2, nbits = 2048):
    mol = Chem.MolFromSmiles(smiles)
    fp = None
    if mol:
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nbits)
    return fp

def calc_similarity(smiles_pairs, nbits = 2048):
    sims = []
    for start, end in smiles_pairs:
        fp_start = calc_fingerprint(start, nbits=nbits)
        fp_end = calc_fingerprint(end, nbits=nbits)
        if fp_start == None or fp_end == None:
            continue
        sims.append(DataStructs.TanimotoSimilarity(fp_start, fp_end))
    return np.mean(sims) if len(sims) > 0 else 0

def validate_smiles(smiles: str,
                    canonicalize=False,
                    return_fingerprint=False,
                    radius=2,
                    nbits=512):
        '''
        Validate SMILES string.

        Parameters
        ----------
        smiles : str
            SMILES string to validate.
        canonicalize : bool, optional
            If True, canonicalize SMILES string.
        return_fingerprint : bool, optional
            If True, return Morgan fingerprint of SMILES string.
        radius : int, optional
            The radius of the Morgan fingerprint.
        nbits : int, optional
            The number of bits in the Morgan fingerprint.
        '''
        valid_smiles = smiles
        is_valid = True

        mol = Chem.MolFromSmiles(smiles)
        fp = None
        if mol:
            if canonicalize:
                valid_smiles = Chem.MolToSmiles(mol, canonical=True)
            else:
                valid_smiles = smiles

            if return_fingerprint:
                fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nbits)
                fp = np.frombuffer(fp.ToBitString().encode(), 'b1')
        else:
            is_valid = False
            if return_fingerprint:
                fp = np.zeros(nbits, dtype=bool)

        if fp is not None:
            return valid_smiles, is_valid, fp
        else:
            return valid_smiles, is_valid
