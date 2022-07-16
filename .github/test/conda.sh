#!/bin/bash

wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh -O /tmp/miniconda.sh
/bin/bash /tmp/miniconda.sh -b
export PATH=$PATH:/home/gitpod/miniconda3/bin
conda init bash
eval "$(conda shell.bash hook)"
conda install -c conda-forge wxpython -y
pip install -r requirements.txt