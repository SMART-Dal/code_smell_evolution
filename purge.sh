#!/bin/bash
#SBATCH --job-name=evo-purge
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8

#SBATCH --time=15:00          # Process limit for each task

#SBATCH --account=def-tusharma
#SBATCH --mail-user=gautam@dal.ca
#SBATCH --mail-type=ALL

repo_name="code_smell_evolution_PURGE"


echo ">>> JOB STARTED FOR $repo_name"

# -------------------------------------------------------
echo ">>> Loading modules and activating virtual environment."
module --force purge
module load StdEnv/2020 python/3.10

virtualenv --no-download $SLURM_TMPDIR/.venv
source $SLURM_TMPDIR/.venv/bin/activate
pip install --no-index --upgrade pip
# -------------------------------------------------------

# -------------------------------------------------------
echo -e "\n\n\n\n\n>>> Executing the purge script."
# -u is for unbuffered output so the print statements print it to the slurm out file
# & at the end is to run the script in background. Unless it's running in background we can't trap the signal
python -u scripts/purge.py &

PID=$!
wait ${PID}
# -------------------------------------------------------

# -------------------------------------------------------
echo ">>> Unloading modules and deactivating virtual environment."
deactivate
module unload python/3.10 java/17.0.2 StdEnv/2020
echo ">>> JOB ENDED FOR $repo_name"