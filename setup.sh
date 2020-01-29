#!/bin/bash

# This file will make the slurmify.py script executable by adding the Slurmify base directory
# to your PATH

# Add to PATH
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo PATH=$DIR:$PATH >> ~/.bashrc
source ~/.bashrc
