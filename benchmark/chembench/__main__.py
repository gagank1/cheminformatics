import os
import logging
import hydra
import pandas as pd

from datetime import datetime
from pydoc import locate
from collections import OrderedDict
from chembench.data.cache import DatasetCacheGenerator

log = logging.getLogger(__name__)


def convert_runtime(time_):
    return time_.seconds + (time_.microseconds / 1.0e6)


def save_metric_results(file_path, metric_list, return_predictions):
    '''
    Saves metrics into a CSV file.
    '''
    metric_df = pd.concat(metric_list, axis=1).T
    if return_predictions:
        pickle_file = file_path + '.pkl'
        log.info(f'Writing predictions to {pickle_file}...')

        if os.path.exists(pickle_file):
            pickle_df = pd.read_pickle(pickle_file)
            pickle_df = pd.concat([pickle_df, metric_df], axis=0)
        else:
            pickle_df = metric_df

        pickle_df.to_pickle(pickle_file)

    if 'predictions' in metric_df.columns:
        metric_df.drop('predictions', inplace=True, axis=1)

    log.info(metric_df)
    csv_file_path = file_path + '.csv'
    write_header = False if os.path.exists(csv_file_path) else True
    metric_df.to_csv(csv_file_path, index=False, mode='a', header=write_header)


@hydra.main(config_path=".",
            config_name="benchmark_metrics")
def main(cfg):
    os.makedirs(cfg.output.path, exist_ok=True)
    log.info(f'Benchmarking mode {cfg.model.name}')
    inferrer = locate(cfg.model.name)()
    log.setLevel(cfg.log.level)
    ds_generator = DatasetCacheGenerator(inferrer,
                                         db_file=cfg.sampling.db,
                                         batch_size=cfg.model.batch_size)
    # Initialize database with smiles in all datasets
    log.info(f'DB initialization enabled = {cfg.sampling.initialize_db}')
    if cfg.sampling.initialize_db:
        radius = cfg.sampling.radius
        for metric in  cfg.metrics:
            log.info(f'Loading dataset for {metric}...')

            datasets = cfg.metrics[metric].datasets
            num_requested = cfg.sampling.sample_size

            if not cfg.metrics[metric].enabled:
                continue

            for dataset in datasets:
                if hasattr(dataset, 'file'):
                    ds_generator.initialize_db(dataset,
                                               radius,
                                               num_requested=num_requested)
                else:
                    raise ValueError(f'Only {dataset} with file accepted')

    # Fetch samples and embeddings and update database.
    log.info(f'Generating samples and embedding...')
    ds_generator.sample()
    log.setLevel(cfg.log.level)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for metric_name in  cfg.metrics:
        metric = cfg.metrics[metric_name]
        if not metric.enabled:
            continue
        impl = locate(metric.impl)(metric_name, metric, cfg)
        file_path = os.path.join(cfg.output.path,
                                 f'{cfg.model.display_name}-{cfg.exp_name}-{metric_name}')


        variations = impl.variations(result_filename=file_path)
        for variation in variations:
            log.info(f'Processing {metric_name} with parameters {variations}...')
            start_time = datetime.now()
            results = impl.calculate(**variation)
            run_time = convert_runtime(datetime.now() - start_time)

            if not isinstance(results, list):
                results = [results]

            for result in results:
                result['inferrer'] = cfg.model.name
                result['iteration'] = 0
                result['run_time'] = run_time
                result['timestamp'] = timestamp
                result['data_size'] = len(impl)

                # Updates to irregularly used arguments
                key_list = ['model', 'gene', 'remove_invalid', 'n_splits']
                for key in key_list:
                    if key in variation and not key in result:
                        result[key] = variation[key]

                return_predictions = impl.is_prediction()
                result = OrderedDict(sorted(result.items()))
                save_metric_results(file_path,
                                    [pd.Series(result)],
                                    return_predictions=return_predictions)

        impl.cleanup()

if __name__ == '__main__':
    main()