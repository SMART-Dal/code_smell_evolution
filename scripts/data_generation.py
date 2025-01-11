import argparse
import traceback
import os
import datetime
from pathlib import Path
from corpus import prepare_corpus
from runners import Designite, RefMiner
from utils import GitManager, ColoredStr

def execute_designite(username, repo_name, repo_path, branch):
    """
    Collects code smells for a given repository. 
    """
    success = False
    try:
        designite_runner = Designite()
        return_code = designite_runner.analyze_commits(username, repo_name, repo_path, branch)
        
        if return_code != 0:
            success = False
        else:
            success = True
    except Exception as e:
        print(ColoredStr.red(e))
        traceback.print_exc()
    
    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    info_file = os.path.join(designite_runner.output_dir, f"designite_status_{current_time}.txt")
    save_info(info_file, repo_path, branch, success)

def execute_refminer(username, repo_name, repo_path, branch):
    """
    Collects refactorings for a given repository.
    """
    success = False
    try:
        ref_miner_runner = RefMiner(print_log=True)
        ref_miner_runner.analyze(username, repo_name, repo_path, branch)
        success = True
    except Exception as e:
        print(ColoredStr.red(e))
        traceback.print_exc()
    
    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    info_file = os.path.join(ref_miner_runner.output_dir, f"refminer_status_{current_time}.txt")
    save_info(info_file, repo_path, branch, success)
        
def save_info(info_file: str, repo_path: Path, branch: str, success: bool):
    
    file_exists = os.path.exists(info_file)
    with open(info_file, "a") as f:
        if not file_exists:
            # Write header row if file doesn't exist
            f.write("Repo Path,Branch,Success\n")
        
        # Append the new row of data
        f.write(f"{repo_path},{branch},{success}\n")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run analysis on repo index")
    parser.add_argument("tool", type=str, help="tool to use for analysis")
    parser.add_argument("idx", type=int, help="index of the repository to process.")
    args = parser.parse_args()
    

    TOOL = args.tool
    REPO_IDX = args.idx
    
    CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    repo = prepare_corpus(REPO_IDX, clone=False)
    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    (username, repo_name, repo_path) = repo
    default_branch = GitManager.get_default_branch(repo_path)
    
    if default_branch:
        if TOOL == "designite":
            execute_designite(username, repo_name, repo_path, branch=default_branch)
        elif TOOL == "refminer":
            execute_refminer(username, repo_name, repo_path, branch=default_branch)
    else:
        print(ColoredStr.red(f"Failed to get default branch for repo: {repo_path}"))
        
            
        