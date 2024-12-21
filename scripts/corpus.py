import os
import config
from utils import GitManager, load_json_file

def prepare_corpus(items_limit = -1):
    if not os.path.exists(config.CORPUS_PATH):
        os.makedirs(config.CORPUS_PATH)
    
    repo_items: list = load_json_file(config.CORPUS_LIST_PATH).get("items")
    if items_limit != -1:
        repo_items = repo_items[:items_limit]
    corpus_info = {}
    
    try:
        for repo in repo_items:
            username, repo_name = repo.get("name").split("/")
            GitManager.clone_repo(
                repo_path=os.path.join(config.CORPUS_PATH, username, repo_name),
                repo_full_name=repo.get("name")
            )
            if username not in corpus_info:
                corpus_info[username] = []
            corpus_info[username].append(repo_name)
                
    except Exception as e:
        print(e)
        
    return corpus_info

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
    print(prepare_corpus(items_limit=5))