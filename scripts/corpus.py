import os
import config
from utils import GitManager, load_json_file, save_json_file
import datetime

def prepare_corpus(start_index=0, end_index=-1):
    if not os.path.exists(config.CORPUS_PATH):
        os.makedirs(config.CORPUS_PATH)
    
    repo_items: list = load_json_file(config.CORPUS_LIST_PATH).get("items")
    if end_index != -1:
        repo_items = repo_items[start_index:end_index]
    else:
        repo_items = repo_items[start_index:]
    
    try:
        for repo in repo_items:
            username, repo_name = repo.get("name").split("/")
            repo_path = os.path.join(config.CORPUS_PATH, username, repo_name)
            GitManager.clone_repo(
                repo_path=repo_path,
                repo_full_name=repo.get("name")
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