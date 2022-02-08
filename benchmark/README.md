# Getting started

## Option 1 - Using existing container
This is the easiest method to execute benchmark tests using packaged models.

### Step 1 - Start container
Depending on the model to be benchmarked start container using `launch.sh`
```
# For benchmarking MegaMolBART
./launch.sh dev 2

# For benchmarking CDDD
./launch.sh dev 1
```

### Step 2 - Start benchmark test
To start a benchmark task
```
python3 -m cuchembm --config-dir /workspace/benchmark/scripts/
```

### TIP - To start a run in a container in daemon mode please execute the following command

```
# For benchmarking MegaMolBART
./launch.sh dev 2 "python3 -m cuchembm --config-dir /workspace/benchmark/scripts/"
```
<hr>
<br>

## Option 2 - Setup a clean environment(container/baremetal)
This is recommended for benchmarking any unsupported generative model using this module. This section explains setting up prerequisites for the benchmark module alone. Additional steps will be required to set up inference capabilities.

### Step 1 - Create Conda environment
Please use the [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html#installing-in-silent-mode) at ./conda/env.yml

```
conda env create -f ./conda/env.yml
```

### Step 2 - Install benchmark module
```
pip install .
```

### Step 3 - Install prerequisites for inferencing the model
Please install the software prerequisites and implement a class with following structure for inferencing the model

```python

class SomeModelInferenceWrapper():

    def __init__(self) -> None:

    def is_ready(self, timeout: int = 10) -> bool:

    def smiles_to_embedding(self, smiles: str, padding: int,
                            scaled_radius=None, num_requested: int = 10,
                            sanitize=True):

    def embedding_to_smiles(self, embedding, dim: int, pad_mask):

    def find_similars_smiles(self, smiles: str, num_requested: int = 10,
                             scaled_radius=1, force_unique=False,
                             sanitize=True):

    def interpolate_smiles(self, smiles: List, num_points: int = 10,
                           scaled_radius=None, force_unique=False,
                           sanitize=True):
```

<hr>
<br>
<br>

# Configuration

```yaml
formatters:
  simple:
    format: '%(asctime)s %(name)s [%(levelname)s]: %(message)s'
handlers:
  console:
    class: logging.StreamHandler
    formatter: simple
    stream: ext://sys.stdout

root:
  handlers: [console]

model:

  name:  cuchembm.inference.SomeModelInferenceWrapper
  training_data: /data/db/zinc_train.sqlite3

sampling:
  max_seq_len: 512
  sample_size: 10
  db: /data/db/samples_db_.sqlite3 # This is used to store intermediate values
  concurrent_requests: 8

output:
  path: /data/benchmark_output/

metric:
  validity:
    enabled: True
    input_size: 20000
    radius:
      - 0.75

  unique:
    enabled: True
    input_size: ${metric.validity.input_size}
    remove_invalid: False
    radius: ${metric.validity.radius}

  novelty:
    enabled: True
    input_size: ${metric.validity.input_size}
    remove_invalid: True
    radius: ${metric.validity.radius}

  nearest_neighbor_correlation:
    enabled: True
    input_size: -1
    top_k:
      - 50
      - 100
      - 500

  modelability:
    physchem:
      enabled: True
      input_size: -1
      n_splits: 20
      normalize_inputs: True
      return_predictions: True

    bioactivity:
      enabled: True
      input_size: -1 # Number of genes to include, not number of molecules, -1 is all genes
      gene_cnt: -1
      n_splits: 20
      normalize_inputs: True
      return_predictions: True

```