import argparse
import traceback
import os
import config
import datetime
from pathlib import Path
from corpus import prepare_corpus
from runners import Designite, RefMiner
from utils import GitManager, ColoredStr, save_json_file, load_json_file

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
    
    info_file = os.path.join(designite_runner.output_dir, "designite_log.txt")
    save_info(info_file, repo_path, branch, success)

def execute_refminer(username, repo_name, repo_path, branch):
    """
    Collects refactorings for a given repository.
    """
    success = False
    try:
        ref_miner_runner = RefMiner()
        ref_miner_runner.analyze(username, repo_name, repo_path, branch)
        success = True
    except Exception as e:
        print(ColoredStr.red(e))
        traceback.print_exc()
        
    info_file = os.path.join(ref_miner_runner.output_dir, "refminer_log.txt")
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
    parser = argparse.ArgumentParser(description="Run analysis on a range of repositories.")
    parser.add_argument("start", type=int, help="Start index of the repositories to process.")
    parser.add_argument("end", type=int, help="End index of the repositories to process.")
    args = parser.parse_args()

    START_INDEX = args.start
    END_INDEX = args.end
    
    CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    corpus_generator = prepare_corpus(START_INDEX, END_INDEX)
    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    corpus_info: dict[str, list[str]] = {}
    corpus_info_filename = f"corpus_info_{current_time}.json"
    
    for username, repo_name, repo_path in corpus_generator:
        corpus_info.update(load_json_file(os.path.join(config.CORPUS_PATH, corpus_info_filename)))
        if username not in corpus_info:
            corpus_info[username] = []
        corpus_info[username].append(repo_name)
            
        default_branch = GitManager.get_default_branch(repo_path)
        if not default_branch:
            print(ColoredStr.red(f"Failed to get default branch for repo: {repo_path}"))
            continue
        
        save_json_file(os.path.join(config.CORPUS_PATH, corpus_info_filename), corpus_info)
        execute_designite(username, repo_name, repo_path, branch=default_branch)
        execute_refminer(username, repo_name, repo_path, branch=default_branch)
            
        