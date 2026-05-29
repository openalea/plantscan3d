# Installation

You must use conda environment : <https://docs.conda.io/en/latest/index.html>

## Users

### Create a new environment with plantscan3d installed in there

```bash

mamba create -n plantscan3d -c openalea3 -c conda-forge  openalea.plantscan3d
mamba activate plantscan3d
```

Install plantscan3d in a existing environment

```bash
mamba install -c openalea3 -c conda-forge openalea.plantscan3d
```

### (Optional) Test your installation

```bash
mamba install -c conda-forge pytest
git clone https://github.com/openalea/plantscan3d.git
cd plantscan3d/test; pytest
```

## Developers

### Install From source

```bash
# Install dependency with conda
mamba env create -f conda/environment.yml
mamba activate plantscan3d_dev

# Clone plantscan3d and install
git clone https://github.com/openalea/plantscan3d.git
cd plantscan3d
pip install .

# (Optional) Test your installation
cd test; pytest
```
