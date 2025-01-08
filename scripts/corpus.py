import os
import config
from utils import GitManager, load_json_file, save_json_file
import datetime

def prepare_corpus(repo_index=None):
    if repo_index is None:
        raise ValueError("repo_index must be provided")
    
    if not os.path.exists(config.CORPUS_PATH):
        os.makedirs(config.CORPUS_PATH)
    
    repo_items: list = load_json_file(config.CORPUS_LIST_PATH).get("items", [])
    
    #sort by commits ascending
    repo_items = sorted(repo_items, key=lambda x: x.get("commits", 0))
    
    if repo_index < 0 or repo_index >= len(repo_items):
        raise IndexError(f"repo_index {repo_index} is out of range")
    
    repo_item = repo_items[repo_index]
    
    try:
        username, repo_name = repo_item.get("name").split("/")
        repo_path = os.path.join(config.CORPUS_PATH, username, repo_name)
        GitManager.clone_repo(
            repo_path=repo_path,
            repo_full_name=repo_item.get("name")
        )
        
        yield username, repo_name, repo_path
                
    except Exception as e:
        print(e)
        

def prepare_from_corpus_info(corpus_info: dict):
    if not os.path.exists(config.CORPUS_PATH):
        os.makedirs(config.CORPUS_PATH)
        
    try:
        for username, repos in corpus_info.items():
            for repo in repos:
                GitManager.clone_repo(
                    repo_path=os.path.join(config.CORPUS_PATH, username, repo),
                    repo_full_name=f"{username}/{repo}"
                )
                
    except Exception as e:
        print(e)
    
if __name__ == "__main__":
    corpus_info = prepare_corpus(0, 3)
    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"corpus_info_{current_time}.json"
    save_json_file(os.path.join(config.CORPUS_PATH, filename), corpus_info)