#!/bin/bash

# Get current directory of this file
CURR=$PWD
# Add POET & Minigrid-World to Python PATH
export PYTHONPATH=${PYTHONPATH}:${CURR}/POET/poet_distributed
export PYTHONPATH=${PYTHONPATH}:${CURR}/gym-minigrid/gym-minigrid
