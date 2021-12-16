#!/usr/bin/env python3

import logging
import pandas as pd
import numpy as np
from sklearn.model_selection import ParameterGrid, KFold
from cuchembm.data.memcache import Cache

logger = logging.getLogger(__name__)

try:
    import cupy as xpy
    import cudf as xdf
    from cuml.metrics import pairwise_distances, mean_squared_error
    from cuml.linear_model import LinearRegression, ElasticNet
    from cuml.svm import SVR
    from cuml.ensemble import RandomForestRegressor
    from cuchemcommon.utils.metrics import spearmanr
    from cuchem.utils.distance import tanimoto_calculate
    from cuml.experimental.preprocessing import StandardScaler
    RAPIDS_AVAILABLE = True
    logger.info('RAPIDS installation found. Using cupy and cudf where possible.')
except ModuleNotFoundError as e:
    logger.info('RAPIDS installation not found. Numpy and pandas will be used instead.')
    import numpy as xpy
    import pandas as xdf
    from sklearn.metrics import pairwise_distances, mean_squared_error
    from sklearn.linear_model import LinearRegression, ElasticNet
    from sklearn.svm import SVR
    from sklearn.ensemble import RandomForestRegressor
    from scipy.stats import spearmanr
    from cuchem.utils.distance import tanimoto_calculate
    from sklearn.preprocessing import StandardScaler
    RAPIDS_AVAILABLE = False

__all__ = ['NearestNeighborCorrelation', 'Modelability']


def get_model_dict():
    lr_estimator = LinearRegression(normalize=False) # Normalization done by StandardScaler
    lr_param_dict = {'normalize': [False]}

    en_estimator = ElasticNet(normalize=False)
    en_param_dict = {'alpha': [0.001, 0.01, 0.1, 1.0, 10.0, 100],
                     'l1_ratio': [0.0, 0.2, 0.5, 0.7, 1.0]}

    sv_estimator = SVR(kernel='rbf') # cache_size=4096.0 -- did not seem to improve runtime
    sv_param_dict = {'C': [1.75, 5.0, 7.5, 10.0, 20.0],
                     'gamma': [0.0001, 0.001, 0.01, 0.1, 1.0],
                     'epsilon': [0.001, 0.01, 0.1, 0.3],
                     'degree': [3, 5, 7, 9]}
    if RAPIDS_AVAILABLE:
        rf_estimator = RandomForestRegressor(accuracy_metric='mse', random_state=0) # n_streams=12 -- did not seem to improve runtime
    else:
        rf_estimator = RandomForestRegressor(criterion='mse', random_state=0)
    rf_param_dict = {'n_estimators': [10, 50, 100, 150, 200]}

    return {'linear_regression': [lr_estimator, lr_param_dict],
            'elastic_net': [en_estimator, en_param_dict],
            'support_vector_machine': [sv_estimator, sv_param_dict],
            'random_forest': [rf_estimator, rf_param_dict]
            }

class BaseEmbeddingMetric():
    name = None

    """Base class for metrics based on embedding datasets"""
    def __init__(self, inferrer, sample_cache, dataset):
        self.name = self.__class__.__name__
        self.inferrer = inferrer
        self.sample_cache = sample_cache

        self.dataset = dataset
        self.smiles_dataset = dataset.smiles
        self.fingerprint_dataset = dataset.fingerprints
        self.smiles_properties = dataset.properties

    def variations(self):
        return NotImplemented

    def _find_embedding(self,
                        smiles,
                        max_seq_len):

        # Check db for results from a previous run
        embedding_results = self.sample_cache.fetch_embedding_data(smiles)
        if not embedding_results or len(embedding_results[1]) == 1:
            # Generate new samples and update the database
            embedding_results = self.inferrer.smiles_to_embedding(smiles,
                                                                  max_seq_len)
            embedding = embedding_results.embedding
            embedding_dim = embedding_results.dim

            self.sample_cache.insert_embedding_data(smiles,
                                                    embedding_results.embedding,
                                                    embedding_results.dim)
        else:
            # Convert result to correct format
            embedding, embedding_dim = embedding_results
        return embedding, embedding_dim

    def encode(self, smiles, zero_padded_vals, average_tokens, max_seq_len=None):
        """Encode a single SMILES to embedding from model"""
        embedding, dim = self._find_embedding(smiles, max_seq_len)
        embedding = xpy.array(embedding).reshape(dim).squeeze()

        if zero_padded_vals:
            if dim == 2:
                embedding[len(smiles):, :] = 0.0
            else:
                embedding[len(smiles):] = 0.0

        if average_tokens:
            embedding = embedding[:len(smiles)].mean(axis=0).squeeze()
        else:
            embedding = embedding.flatten()

        return embedding

    def _calculate_metric(self):
        raise NotImplementedError

    def encode_many(self, max_seq_len=None, zero_padded_vals=True, average_tokens=False):
        # Calculate pairwise distances for embeddings

        if not max_seq_len:
            max_seq_len = self.dataset.max_seq_len

        embeddings = []
        for smiles in self.smiles_dataset['canonical_smiles']:
            embedding = self.encode(smiles, zero_padded_vals, average_tokens, max_seq_len=max_seq_len)
            embeddings.append(embedding)

        return embeddings

    def calculate(self):
        raise NotImplementedError


class NearestNeighborCorrelation(BaseEmbeddingMetric):
    """Sperman's Rho for correlation of pairwise Tanimoto distances vs Euclidean distance from embeddings"""
    name = 'nearest neighbor correlation'

    def __init__(self, inferrer, sample_cache, smiles_dataset):
        super().__init__(inferrer, sample_cache, smiles_dataset)
        self.name = NearestNeighborCorrelation.name

    def variations(self, cfg, **kwargs):
        top_k_list = list(cfg.metric.nearest_neighbor_correlation.top_k)
        top_k_list = [int(x) for x in top_k_list]
        return {'top_k': top_k_list}

    def _calculate_metric(self, embeddings, fingerprints, top_k=None):
        embeddings_dist = pairwise_distances(embeddings)
        del embeddings

        fingerprints_dist = tanimoto_calculate(fingerprints, calc_distance=True)
        del fingerprints

        corr = spearmanr(fingerprints_dist, embeddings_dist, top_k=top_k)
        return corr

    def calculate(self, top_k=None, **kwargs):

        embeddings = self.encode_many(zero_padded_vals=True,
                                      average_tokens=False)
        embeddings = xpy.asarray(embeddings)
        fingerprints = xpy.asarray(self.fingerprint_dataset)

        metric = self._calculate_metric(embeddings, fingerprints, top_k)
        metric = xpy.nanmean(metric)
        if RAPIDS_AVAILABLE:
            metric = xpy.asnumpy(metric)

        top_k = embeddings.shape[0] - 1 if not top_k else top_k

        return {'name': self.name, 'value': metric, 'top_k': top_k}


class Modelability(BaseEmbeddingMetric):
    """Ability to model molecular properties from embeddings vs Morgan Fingerprints"""
    name = 'modelability'

    def __init__(self, name, inferrer, sample_cache, dataset, n_splits=4, return_predictions=False, normalize_inputs=False):
        super().__init__(inferrer, sample_cache, dataset)
        self.name = name
        self.model_dict = get_model_dict()
        self.n_splits = n_splits
        self.return_predictions = return_predictions
        if normalize_inputs:
            self.norm_data, self.norm_prop = StandardScaler(), StandardScaler()
        else:
            self.norm_data, self.norm_prop = False, False

    def variations(self, model_dict=None, **kwargs):
        if model_dict:
            self.model_dict = model_dict
        return {'model': list(self.model_dict.keys())}

    def gpu_gridsearch_cv(self, estimator, param_dict, xdata, ydata):
        """Perform grid search with cross validation and return score"""
        logger.info(f"Validating input shape {xdata.shape[0]} == {ydata.shape[0]}")
        assert xdata.shape[0] == ydata.shape[0]

        best_score, best_param, best_pred = np.inf, None, None
        # TODO -- if RF method throws errors with large number of estimators, can prune params based on dataset size.
        for param in ParameterGrid(param_dict):
            estimator.set_params(**param)
            logging.debug(f"Grid search param {param}")

            # Generate CV folds
            kfold_gen = KFold(n_splits=self.n_splits, shuffle=True, random_state=0)
            kfold_mse = []
            for train_idx, test_idx in kfold_gen.split(xdata, ydata):
                xtrain, xtest, ytrain, ytest = xdata[train_idx], xdata[test_idx], ydata[train_idx], ydata[test_idx]

                estimator.fit(xtrain, ytrain)
                ypred = estimator.predict(xtest)
                mse = mean_squared_error(ypred, ytest).item() # NOTE: convert to negative MSE and maximize metric if SKLearn GridSearch is ever used
                kfold_mse.append(mse)

            avg_mse = np.nanmean(np.array(kfold_mse))
            if avg_mse < best_score:
                best_score, best_param = avg_mse, param
                if self.return_predictions:
                    best_pred = estimator.predict(xdata)
        return best_score, best_param, best_pred

    def _calculate_metric(self, embeddings, fingerprints, estimator, param_dict):
        """Perform grid search for each metric and calculate ratio"""
        properties = self.smiles_properties
        assert len(properties.columns) == 1
        prop_name = properties.columns[0]
        properties = xpy.asarray(properties[prop_name], dtype=xpy.float32)

        if self.norm_data:
            embeddings = self.norm_data.fit_transform(embeddings)
        if self.norm_prop:
            properties = self.norm_prop.fit_transform(properties[xpy.newaxis, :]).squeeze()

        embedding_error, embedding_param, embedding_pred = self.gpu_gridsearch_cv(estimator, param_dict, embeddings, properties)
        fingerprint_error, fingerprint_param, fingerprint_pred = self.gpu_gridsearch_cv(estimator, param_dict, fingerprints, properties)

        if self.return_predictions & RAPIDS_AVAILABLE:
            embedding_pred, fingerprint_pred = xpy.asnumpy(embedding_pred), xpy.asnumpy(fingerprint_pred)

        ratio = fingerprint_error / embedding_error # If ratio > 1.0 --> embedding error is smaller --> embedding model is better

        if (self.norm_prop is not None) & self.return_predictions:
            fingerprint_pred = self.norm_prop.inverse_transform(fingerprint_pred[xpy.newaxis, :]).squeeze()
            embedding_pred = self.norm_prop.inverse_transform(embedding_pred[xpy.newaxis, :]).squeeze()

        results = {'value': ratio, 
                   'fingerprint_error': fingerprint_error, 
                   'embedding_error': embedding_error, 
                   'fingerprint_param': fingerprint_param, 
                   'embedding_param': embedding_param,
                   'predictions': {'fingerprint_pred': fingerprint_pred, 
                                   'embedding_pred': embedding_pred} }
        return results

    def calculate(self, estimator, param_dict, **kwargs):

        # TODO DEBUG RAJESH
        embeddings = self.encode_many(zero_padded_vals=False, average_tokens=True)
        # embeddings = Cache().get_data('embeddings')
        # if embeddings is None:
        #     logger.info("Retrieving embeddings...")
        #     embeddings = self.encode_many(zero_padded_vals=False, average_tokens=True)
        #     Cache().set_data('embeddings', embeddings)

        embeddings = xpy.asarray(embeddings, dtype=xpy.float32)
        fingerprints = xpy.asarray(self.fingerprint_dataset.values, dtype=xpy.float32)

        logger.info("Computing metric...")
        results = self._calculate_metric(embeddings,
                                         fingerprints,
                                         estimator,
                                         param_dict)
        results['property'] = self.smiles_properties.columns[0]
        results['name'] = self.name
        return results