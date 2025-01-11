#!/bin/bash

SLURM_TMPDIR=$1

echo ">>> Installing PyDriller at $SLURM_TMPDIR"

# Copy the PyDriller submodule repository
cp -R bin/packages/pydriller/ $SLURM_TMPDIR/pydriller

# Install PyDriller
pip install $SLURM_TMPDIR/pydriller
