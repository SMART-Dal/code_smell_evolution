import argparse
import traceback
import os
import config
import shutil
from corpus import prepare_corpus
from runners import Designite, RefMiner
from utils import GitManager, ColoredStr
from zip import zip_dir

def execute_designite(idx, username, repo_name, repo_path, branch):
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

    if success:
        try:
            target_dir = os.path.join(config.OUTPUT_PATH, 'Designite_OP', username, repo_name)
            if not os.path.exists(target_dir):
                print(f"Error: Target path '{target_dir}' does not exist.")
                exit(1)
            
            zip_dir(target_dir, os.path.join(config.ZIP_LIB, f'smells_{idx}.zip'))
            
            # Flush the smells dataset directory after zipping
            shutil.rmtree(target_dir)
            print(f"Flushed smells dataset directory: {target_dir}")
        except Exception as e:
            print(ColoredStr.red(e))
            traceback.print_exc()
        

def execute_refminer(idx, username, repo_name, repo_path, branch):
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
        
    if success:
        try:
            target_dir = os.path.join(config.OUTPUT_PATH, 'RefMiner_OP', username)
            if not os.path.exists(target_dir):
                print(f"Error: Target path '{target_dir}' does not exist.")
                exit(1)
            
            zip_dir(target_dir, os.path.join(config.ZIP_LIB, f'refs_{idx}.zip')) 
            
            # Flush the refactoring dataset directory after zipping
            if os.path.isdir(target_dir):
                shutil.rmtree(target_dir)
                print(f"Flushed refactoring dataset directory: {target_dir}")
            else:
                os.remove(target_dir)
                print(f"Flushed refactoring dataset file: {target_dir}")
        except Exception as e:
            print(ColoredStr.red(e))
            traceback.print_exc()
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run analysis on repo index")
    parser.add_argument("tool", type=str, help="tool to use for analysis")
    parser.add_argument("idx", type=int, help="index of the repository to process.")
    args = parser.parse_args()

    TOOL = args.tool
    REPO_IDX = args.idx
    
    CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    
    (username, repo_name, repo_path) = prepare_corpus(REPO_IDX, clone=False)
    default_branch = GitManager.get_default_branch(repo_path)
    
    if default_branch:
        if TOOL == "designite":
            execute_designite(REPO_IDX, username, repo_name, repo_path, branch=default_branch)
        elif TOOL == "refminer":
            execute_refminer(REPO_IDX, username, repo_name, repo_path, branch=default_branch)
    else:
        print(ColoredStr.red(f"Failed to get default branch for repo: {repo_path}"))
        traceback.print_exc()
        
            
        