#!/bin/bash
#SBATCH --job-name=evo-clct-smell
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8

#SBATCH --mem-per-cpu=32G
#SBATCH --array=0-4             # Array range for 6 tasks
#SBATCH --time=4:00:00          # Process limit for each task

#SBATCH --account=def-tusharma
#SBATCH --mail-user=gautam@dal.ca
#SBATCH --mail-type=ALL

repo_name="code_smell_evolution_collect_smell"

# Define the list of single integer arguments for the 6 tasks
ARG_VALUES=(11 12 13 14 15)

# Get the argument for this task ID
ARG=${ARG_VALUES[$SLURM_ARRAY_TASK_ID]}

echo ">>> JOB STARTED FOR $repo_name (Task ID: $SLURM_ARRAY_TASK_ID with ARG: $ARG)"
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
unset JAVA_TOOL_OPTIONS

virtualenv --no-download $SLURM_TMPDIR/.venv
source $SLURM_TMPDIR/.venv/bin/activate
pip install --no-index --upgrade pip
pip install  --no-index -r requirements.txt
# -------------------------------------------------------

# Clone the pydriller repository
# echo ">>> Cloning pydriller repository into tmp directory."
# git clone https://github.com/ishepard/pydriller.git $SLURM_TMPDIR/pydriller
cp -R pydriller/ $SLURM_TMPDIR/pydriller 

# Install pydriller
echo ">>> Installing pydriller."
pip install $SLURM_TMPDIR/pydriller

# -------------------------------------------------------
echo -e "\n\n\n\n\n>>> Executing the script."
# -u is for unbuffered output so the print statements print it to the slurm out file
# & at the end is to run the script in background. Unless it's running in background we can't trap the signal
python -u scripts/data_generation.py designite $ARG &

PID=$!
wait ${PID}

echo -e ">>> Completed execution of the script.\n\n\n\n\n>>>Attempting to copy the output file..."
rsync -axvH --no-g --no-p $SLURM_TMPDIR/$repo_name/output/*  $refresearch/data/output
# -------------------------------------------------------

# -------------------------------------------------------
echo ">>> Unloading modules and deactivating virtual environment."
deactivate
module unload python/3.10 java/17.0.2 StdEnv/2020
echo ">>> JOB ENDED FOR $repo_name (Task ID: $SLURM_ARRAY_TASK_ID)"