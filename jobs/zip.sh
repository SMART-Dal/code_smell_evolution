#!/bin/bash
#SBATCH --job-name=evo-zip
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8

#SBATCH --mem-per-cpu=8G
#SBATCH --array=0-21             # Array range for 6 tasks
#SBATCH --time=30:00          # Process limit for each task

#SBATCH --account=def-tusharma
#SBATCH --mail-user=gautam@dal.ca
#SBATCH --mail-type=ALL

repo_name="code_smell_evolution_ZIP/UNZIP"

# Define the list of single integer arguments for the 6 tasks
ARG_VALUES=(0 2 3 4 5 6 7 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23)

# Get the arguments for this task ID
MODE="zip"              #choices=["zip", "unzip"]
OUTPUT="refs"         #choices=["smells", "refs"]
ARG=${ARG_VALUES[$SLURM_ARRAY_TASK_ID]}

echo ">>> JOB STARTED FOR $repo_name  (Task ID: $SLURM_ARRAY_TASK_ID with ARG: $ARG)"

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
echo -e "\n\n\n\n\n>>> Executing the zip/unzip script."
# -u is for unbuffered output so the print statements print it to the slurm out file
# & at the end is to run the script in background. Unless it's running in background we can't trap the signal
python -u scripts/zip.py $MODE $OUTPUT $ARG &

PID=$!
wait ${PID}
# -------------------------------------------------------

# -------------------------------------------------------
echo ">>> Unloading modules and deactivating virtual environment."
deactivate
module unload python/3.10
echo ">>> JOB ENDED FOR $repo_name (Task ID: $SLURM_ARRAY_TASK_ID)"