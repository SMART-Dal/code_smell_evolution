#!/bin/bash
#SBATCH --job-name=evo-anlys-manual-analysis-generate-samples
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8

#SBATCH --mem-per-cpu=64G
#SBATCH --time=3:00:00          # Process limit for each task

#SBATCH --account=xxxxx
#SBATCH --mail-user=xxxxx
#SBATCH --mail-type=ALL

repo_name="code_smell_evolution_generate_samples"


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
pip install GitPython matplotlib numpy pandas seaborn  --no-index

# -------------------------------------------------------
echo -e "\n\n\n\n\n>>> Executing the script."
# -u is for unbuffered output so the print statements print it to the slurm out file
# & at the end is to run the script in background. Unless it's running in background we can't trap the signal
python -u scripts/llm_analysis.py &

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