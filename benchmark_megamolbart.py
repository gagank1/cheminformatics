#!/usr/bin/env python3

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import torch
from rdkit import Chem

import sys
sys.path.insert(0, "/workspace/megamolbart")
from megamolbart.inference import MegaMolBART


BENCHMARK_DRUGS_PATH = '/workspace/cuchem/tests/data/benchmark_approved_drugs.csv'
BENCHMARK_OUTPUT_PATH = '/workspace/megamolbart/benchmark'


def validate_smiles_list(smiles_list):
    """Ensure SMILES are valid and sanitized, otherwise fill with NaN."""
    smiles_clean_list = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles, sanitize=True)
        if mol:
            sanitized_smiles = Chem.MolToSmiles(mol)
        else:
            sanitized_smiles = np.NaN
        smiles_clean_list.append(sanitized_smiles)

    return smiles_clean_list


def do_sampling(data, func, num_samples, radius_list, radius_scale):
    """Sampling for single molecule and interpolation between two molecules."""
    smiles_results = list()
    for radius in radius_list:
        simulated_radius = radius / radius_scale
        
        for smiles in data:
            smiles_df = func(smiles, num_samples, radius=simulated_radius)

            smiles_df = smiles_df[smiles_df['Generated']]
            # All molecules are valid and not the same as input
            smiles_df = pd.DataFrame({'OUTPUT': validate_smiles_list(smiles_df['SMILES'].tolist())})
            if not isinstance(smiles, list):
                smiles = [smiles]
            mask = smiles_df['OUTPUT'].isin(smiles).pipe(np.invert)
            smiles_df = smiles_df[mask]
            smiles_df['INPUT'] = ','.join(smiles)
            smiles_df['RADIUS'] = radius
            smiles_results.append(smiles_df)

    smiles_results = pd.concat(smiles_results, axis=0).reset_index(drop=True)[['RADIUS', 'INPUT', 'OUTPUT']]
    return smiles_results


def calc_statistics(df, level):
    """Calculate validity and uniqueness statistics per molecule or per radius / sampling type"""
    def _percent_valid(df):
        return len(df.dropna()) / float(len(df))
    
    def _percent_unique(df):
        return len(set(df.dropna().tolist())) / float(len(df))
    
    results = df.groupby(level=level).agg([_percent_valid, _percent_unique])
    results.columns = ['percent_valid', 'percent_unique']
    return results


def plot_results(overall):
    """Plot the overall data statistics"""
    fig, axList = plt.subplots(ncols=2, nrows=1)
    fig.set_size_inches(10, 6)
    for ax, sample, kind in zip(axList, ['interp', 'single'], ['bar', 'line']):
        plt_data = overall.loc[sample]
        plt_data.plot(kind=kind, ax=ax)
        ax.set(title=f'Latent Space Sampling Type: {sample.title()}')    
        if sample == 'single':
            ax.set(xlabel='Radius', ylabel='Percent')
        else:
            ax.set(xlabel='', ylabel='Percent')
            ax.set_xticklabels([])
    fig.savefig(os.path.join(BENCHMARK_OUTPUT_PATH, 'overall.png'))


if __name__ == '__main__':

    # num_molecules = 10
    # num_samples = 10
    # radius_list = [0.00001, 0.00005, 0.0001, 0.0005, 0.001]  
    num_molecules = 2
    num_samples = 5
    radius_list = [0.00001, 0.00005]    
    data = pd.read_csv(BENCHMARK_DRUGS_PATH)

    with torch.no_grad():
        wf = MegaMolBART()
        master_df = list()
        for sample_type in ['single', 'interp']:

            # func is what controls which sampling is used
            if sample_type == 'single':
                sampled_data = data['canonical_smiles'].sample(n=num_molecules, replace=False, random_state=0).tolist()
                func = wf.find_similars_smiles
                smiles_results = do_sampling(sampled_data, func, num_samples, radius_list, wf.radius_scale)
            else:
                # Sample two at a time -- must ensure seed is different each time
                sampled_data = [data['canonical_smiles'].sample(n=2, replace=False, random_state=i).tolist() for i in range(num_molecules)]
                func = wf.interpolate_from_smiles
                # radius not used for sampling two at a time -- enter dummy here
                smiles_results = do_sampling(sampled_data, func, num_samples, [1.0], 1.0)
                #smiles_results['RADIUS'] = np.NaN

            smiles_results['SAMPLE'] = sample_type
            master_df.append(smiles_results)
    
    indexes = ['SAMPLE', 'RADIUS', 'INPUT']
    master_df = pd.concat(master_df, axis=0).set_index(indexes)
    results = calc_statistics(master_df, indexes)
    overall = calc_statistics(master_df, indexes[:-1])

    with open(os.path.join(BENCHMARK_OUTPUT_PATH, 'results.md'), 'w') as fh:
        results.reset_index().to_markdown(fh)
    
    with open(os.path.join(BENCHMARK_OUTPUT_PATH, 'overall.md'), 'w') as fh:
        overall.reset_index().to_markdown(fh)

    plot_results(overall)
    
    

