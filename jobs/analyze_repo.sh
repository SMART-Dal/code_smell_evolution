#!/bin/bash
#SBATCH --job-name=evo-anlys-corpus
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8

#SBATCH --mem-per-cpu=16G
#SBATCH --array=0-19             # Array range for 6 tasks
#SBATCH --time=6:00:00          # Process limit for each task

#SBATCH --account=xxxxx
#SBATCH --mail-user=xxxxx
#SBATCH --mail-type=ALL

repo_name="code_smell_evolution_corpus_analysis"

# Define the list of single integer arguments
ARG_VALUES=(0 2 3 4 5 6 7 9 10 11 12 13 14 15 16 17 18 19 21 22)

# 0 2 3 4 5 6 7 9 10 11 12 13 14 15 16 17 18 19 21 22
# 23 24 25 26 27 28 29 31 32 33 34 35 36 37 39 40 42 43 44 45
# 47 49 50 52 53 54 55 56 58 59 60 62 63 64 65 66 67 68 69 70
# 71 72 73 74 75 76 77 78 79 80 81 82 84 87 88 89 90 91 92 93
# 94 95 96 97 99 103 109 111

ARG=${ARG_VALUES[$SLURM_ARRAY_TASK_ID]}

echo ">>> JOB STARTED FOR $repo_name"
export $SLURM_TMPDIR

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
pip install GitPython matplotlib numpy pandas seaborn chardet --no-index

# -------------------------------------------------------
echo -e "\n\n\n\n\n>>> Executing the script."
# -u is for unbuffered output so the print statements print it to the slurm out file
# & at the end is to run the script in background. Unless it's running in background we can't trap the signal
python -u scripts/analysis.py $ARG &

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