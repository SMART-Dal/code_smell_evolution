import os
import argparse
import config
from utils import GitManager, FileUtils
import datetime
import shutil

def prepare_repo(repo_index=None, clone=True):
    if repo_index is None:
        raise ValueError("repo_index must be provided")
    
    slurm_dir = os.environ.get("SLURM_TMPDIR", None)
    # slurm_dir = "tmp/"
    
    if slurm_dir is None:
        raise RuntimeError("No slurm tmep dir available")
    
    CORPUS_PATH = os.path.join(slurm_dir, "corpus")
        
    if os.path.exists(CORPUS_PATH):
        shutil.rmtree(CORPUS_PATH)
        
    os.makedirs(CORPUS_PATH)
    
    repo_items: list = FileUtils.load_json_file(config.CORPUS_SPECS_PATH).get("items", [])
    
    #sort by commits ascending
    repo_items = sorted(repo_items, key=lambda x: x.get("commits", 0))
    
    if repo_index < 0 or repo_index >= len(repo_items):
        raise IndexError(f"repo_index {repo_index} is out of range")
    
    repo_item = repo_items[repo_index]
    
    try:
        username, repo_name = repo_item.get("name").split("/")
        repo_path = os.path.join(CORPUS_PATH, username, repo_name)
        if clone:
            GitManager.clone_repo(
                repo_path=repo_path,
                repo_full_name=repo_item.get("name")
            )
        
        return username, repo_name, repo_path
                
    except Exception as e:
        print(e)
        return None
    
def flush_repo(repo_index):
    (_, _, repo_path) = prepare_repo(repo_index, clone=False)
    
    try:
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
            print(f"Successfully flushed repository at {repo_path}")
    except Exception as e:
        print(e)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clone repositories from corpus list")
    parser.add_argument("idx", type=int, help="index of the repository to process.")
    args = parser.parse_args()
  
    repo = prepare_repo(repo_index=args.idx)
    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    corpus_info: dict[str, list[str]] = {}
    corpus_info_filename = f"corpus_info_{current_time}.json"
    
    (username, repo_name, repo_path) = repo
    corpus_info.update(FileUtils.load_json_file(os.path.join(config.CORPUS_PATH, corpus_info_filename)))
    if username not in corpus_info:
        corpus_info[username] = []
    corpus_info[username].append(repo_name)
    FileUtils.save_json_file(os.path.join(config.CORPUS_PATH, corpus_info_filename), corpus_info)