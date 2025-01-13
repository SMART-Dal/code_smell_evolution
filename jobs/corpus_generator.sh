#!/bin/bash
#SBATCH --job-name=evo-corpus
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8

#SBATCH --mem-per-cpu=4G
#SBATCH --array=0-3             # Array range for 6 tasks
#SBATCH --time=15:00          # Process limit for each task

#SBATCH --account=def-tusharma
#SBATCH --mail-user=gautam@dal.ca
#SBATCH --mail-type=ALL

repo_name="code_smell_evolution_CORPUS"

repo_indices=(26 27 28 35)

# Get the argument for this task ID
ARG=${repo_indices[$SLURM_ARRAY_TASK_ID]}

echo ">>> JOB STARTED FOR $repo_name"

# -------------------------------------------------------
echo ">>> Loading modules and activating virtual environment."
module --force purge
module load StdEnv/2020 python/3.10

virtualenv --no-download $SLURM_TMPDIR/.venv
source $SLURM_TMPDIR/.venv/bin/activate
pip install --no-index --upgrade pip
pip install  --no-index -r requirements.txt
# -------------------------------------------------------

# -------------------------------------------------------
echo -e "\n\n\n\n\n>>> Cloning corpus at index $ARG." 
# -u is for unbuffered output so the print statements print it to the slurm out file
# & at the end is to run the script in background. Unless it's running in background we can't trap the signal
python -u scripts/corpus.py $ARG &

PID=$!
wait ${PID}
# -------------------------------------------------------

# -------------------------------------------------------
echo ">>> Unloading modules and deactivating virtual environment."
deactivate
module unload python/3.10 StdEnv/2020
echo ">>> JOB ENDED FOR $repo_name"