#!/bin/bash
#SBATCH --job-name=code-smell-evolution
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8

#SBATCH --account=def-tusharma
#SBATCH --mail-user=gautam@dal.ca
#SBATCH --mail-type=ALL
#SBATCH --time=3:00:00

repo_name="code_smell_evolution"

echo ">>> JOB STARTED FOR $repo_name"
handle_signal() 
{
    echo 'Trapped - Moving File'
    rsync -axvH --no-g --no-p $SLURM_TMPDIR/$repo_name/output/* $refresearch/data/output/
    exit 0
}

trap 'handle_signal' SIGUSR1

# -------------------------------------------------------
echo ">>> Loading modules and activating virtual environment."
module --force purge
module load StdEnv/2020 java/17.0.2 python/3.10

export JAVA_TOOL_OPTIONS="-Xms256m -Xmx2g"

virtualenv --no-download $SLURM_TMPDIR/.venv
source $SLURM_TMPDIR/.venv/bin/activate
pip install --no-index --upgrade pip
pip install  --no-index -r requirements.txt
# -------------------------------------------------------

cd pydriller
pip install .
cd ..

# -------------------------------------------------------
echo -e "\n\n\n\n\n>>> Executing the script."
# -u is for unbuffered output so the print statements print it to the slurm out file
# & at the end is to run the script in background. Unless it's running in background we can't trap the signal
python -u scripts/data_generation.py 0 1 &

PID=$!
wait ${PID}

echo -e ">>> Completed execution of the script.\n\n\n\n\n>>>Attempting to copy the output file..."
rsync -axvH --no-g --no-p $SLURM_TMPDIR/$repo_name/output/*  $refresearch/data/output
# -------------------------------------------------------

# -------------------------------------------------------
echo ">>> Unloading modules and deactivating virtual environment."
deactivate
module unload python/3.10 java/17.0.2 StdEnv/2020
echo ">>> JOB ENDED FOR $repo_name"