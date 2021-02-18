#!/opt/conda/envs/rapids/bin/python3
#
# Copyright (c) 2020, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from . import BaseClusterWorkflow
from nvidia.cheminformatics.utils.singleton import Singleton
from nvidia.cheminformatics.config import Context
from nvidia.cheminformatics.utils.metrics import batched_silhouette_scores
from nvidia.cheminformatics.data import ClusterWfDAO
from nvidia.cheminformatics.data.cluster_wf import ChemblClusterWfDao
from nvidia.cheminformatics.utils.logger import MetricsLogger

import cudf
import dask
import dask_cudf
from functools import singledispatch
from typing import List

from cuml.manifold import UMAP as cuUMAP
from cuml.dask.decomposition import PCA as cuDaskPCA
from cuml.dask.cluster import KMeans as cuDaskKMeans
from cuml.dask.manifold import UMAP as cuDaskUMAP


logger = logging.getLogger(__name__)


MIN_RECLUSTER_SIZE = 200


@singledispatch
def _gpu_cluster_wrapper(embedding, n_pca, self):
    return NotImplemented


@_gpu_cluster_wrapper.register(dask.dataframe.core.DataFrame)
def _(embedding, n_pca, self):
    embedding = dask_cudf.from_dask_dataframe(embedding)
    return self._cluster(embedding, n_pca)


@_gpu_cluster_wrapper.register(dask_cudf.core.DataFrame)
def _(embedding, n_pca, self):
    return self._cluster(embedding, n_pca)


@_gpu_cluster_wrapper.register(cudf.DataFrame)
def _(embedding, n_pca, self):
    embedding = dask_cudf.from_cudf(embedding,
                                    chunksize=int(embedding.shape[0] * 0.1))
    return self._cluster(embedding, n_pca)


class GpuKmeansUmap(BaseClusterWorkflow, metaclass=Singleton):

    def __init__(self,
                 n_molecules: int = None,
                 dao: ClusterWfDAO = ChemblClusterWfDao(),
                 pca_comps=64,
                 n_clusters=7,
                 seed=0):

        self.dao = dao
        self.n_molecules = n_molecules
        self.pca_comps = pca_comps
        self.pca = None
        self.n_clusters = n_clusters

        self.df_embedding = None
        self.seed = seed
        self.n_spearman = 5000

    def _cluster(self, embedding, n_pca):
        """
        Generates UMAP transformation on Kmeans labels generated from
        molecular fingerprints.
        """

        dask_client = Context().dask_client
        embedding = embedding.reset_index()
        n_molecules = embedding.compute().shape[0]

        # Before reclustering remove all columns that may interfere
        embedding, prop_series = self._remove_non_numerics(embedding)

        if n_pca and embedding.shape[1] > n_pca:
            with MetricsLogger('pca', n_molecules) as ml:
                if self.pca == None:
                    self.pca = cuDaskPCA(client=dask_client, n_components=n_pca)
                    self.pca.fit(embedding)
                embedding = self.pca.transform(embedding)

        with MetricsLogger('kmeans', n_molecules) as ml:
            if n_molecules < MIN_RECLUSTER_SIZE:
                raise Exception('Reclustering less then %d molecules is not supported.' % MIN_RECLUSTER_SIZE)

            kmeans_cuml = cuDaskKMeans(client=dask_client,
                                    n_clusters=self.n_clusters)
            kmeans_cuml.fit(embedding)
            kmeans_labels = kmeans_cuml.predict(embedding)

            ml.metric_name = 'silhouette_score'
            ml.metric_func = batched_silhouette_scores
            ml.metric_func_args = (embedding, kmeans_labels)
            ml.metric_func_kwargs = {'on_gpu': True,  'seed': self.seed}

        with MetricsLogger('umap', n_molecules) as ml:
            X_train = embedding.compute()

            local_model = cuUMAP()
            local_model.fit(X_train)

            umap_model = cuDaskUMAP(local_model,
                                    n_neighbors=100,
                                    a=1.0,
                                    b=1.0,
                                    learning_rate=1.0,
                                    client=dask_client)
            Xt = umap_model.transform(embedding)

            ml.metric_name = 'spearman_rho'
            ml.metric_func = self._compute_spearman_rho
            ml.metric_func_args = (embedding, X_train, Xt)

        # Add back the column required for plotting and to correlating data
        # between re-clustering
        embedding['cluster'] = kmeans_labels
        embedding['x'] = Xt[0]
        embedding['y'] = Xt[1]

        # Add back the prop columns
        for col in prop_series.keys():
            embedding[col] = prop_series[col]

        return embedding

    def cluster(self, df_mol_embedding=None):

        logger.info("Executing GPU workflow...")

        if df_mol_embedding is None:
            self.n_molecules = Context().n_molecule

            df_mol_embedding = self.dao.fetch_molecular_embedding(
                self.n_molecules,
                cache_directory=Context().cache_directory)

            df_mol_embedding = df_mol_embedding.persist()

        self.df_embedding = _gpu_cluster_wrapper(df_mol_embedding,
                                                 self.pca_comps,
                                                 self)
        return self.df_embedding

    def recluster(self,
                  filter_column=None,
                  filter_values=None,
                  n_clusters=None):

        df_embedding = self.df_embedding
        if filter_values is not None:
            filter = df_embedding[filter_column].isin(filter_values)

            df_embedding['filter_col'] = filter
            df_embedding = df_embedding.query('filter_col == True')

        if n_clusters is not None:
            self.n_clusters = n_clusters

        self.df_embedding = _gpu_cluster_wrapper(df_embedding, None, self)

        return self.df_embedding

    def add_molecules(self, chemblids:List):

        chem_mol_map = {row[0]: row[1] for row in self.dao.fetch_id_from_chembl(chemblids)}
        molregnos = list(chem_mol_map.keys())

        self.df_embedding['id_exists'] = self.df_embedding['id'].isin(molregnos)

        ldf = self.df_embedding.query('id_exists == True')
        if hasattr(ldf, 'compute'):
            ldf = ldf.compute()

        self.df_embedding = self.df_embedding.drop(['id_exists'], axis=1)
        missing_mol = set(molregnos).difference(ldf['id'].to_array())

        chem_mol_map = {id: chem_mol_map[id] for id in missing_mol}

        missing_molregno = chem_mol_map.keys()
        if self.pca and len(missing_molregno) > 0:
            new_fingerprints = self.dao.fetch_molecular_embedding_by_id(missing_molregno)
            new_fingerprints, prop_series = self._remove_non_numerics(new_fingerprints)
            new_fingerprints = self.pca.transform(new_fingerprints)

            # Add back the prop columns
            for col in prop_series.keys():
                new_fingerprints[col] = prop_series[col]

            self.df_embedding = self._remove_ui_columns(self.df_embedding)

            # TODO: Should we maintain the original PCA result for use here
            self.df_embedding = self.df_embedding.append(new_fingerprints)

        return chem_mol_map, molregnos, self.df_embedding