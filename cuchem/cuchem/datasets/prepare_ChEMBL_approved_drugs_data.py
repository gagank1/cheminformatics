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

import os

# import cudf
import numpy as np
import pandas as pd
import pathlib
from cuchemcommon.data.helper.chembldata import ChEmblData
from cuchemcommon.fingerprint import calc_morgan_fingerprints

DATA_BENCHMARK_DIR = os.path.join(pathlib.Path(__file__).absolute().parent.parent.parent,
                                  'tests', 'data')

if __name__ == '__main__':
    results = ChEmblData(fp_type=None).fetch_approved_drugs(with_labels=True)
    benchmark_df = pd.DataFrame(results[0], columns=results[1])

    # TODO: benchmark SMILES have not been explicitly canonicalized with RDKit. Should this be done?
    fp = calc_morgan_fingerprints(benchmark_df)
    fp.columns = fp.columns.astype(np.int64)
    fp.index = fp.index.astype(np.int64)
    for col in fp.columns:
        fp[col] = fp[col].astype(np.float32)

    # Write results
    benchmark_df.to_csv(os.path.join(DATA_BENCHMARK_DIR, 'benchmark_approved_drugs.csv'))
    fp.to_csv(os.path.join(DATA_BENCHMARK_DIR, 'fingerprints_approved_drugs.csv'))
    # fp_hdf5 = cudf.DataFrame(fp)
    # fp_hdf5.to_hdf(os.path.join(DATA_BENCHMARK_DIR, 'filter_00.h5', 'fingerprints', format='table'))
