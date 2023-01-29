#!/bin/bash

wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -O /wine/drive_c/conda_setup.exe
wine cmd.exe /C .github\\entry_build.bat
/entrypoint.sh