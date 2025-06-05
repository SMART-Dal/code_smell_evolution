import os
import traceback
from datetime import datetime

import config
from corpus import prepare_repo, flush_repo
from utils import FileUtils, GitManager
from data_analyzer import RepoDataAnalyzer

def collect_repo_hashes():
    data = {}
    data_output_path = os.path.join(config.BIN_PATH, "data", "corpus_commits.json")
    
    repo_ids = [0, 2, 6]
    
    for idx in repo_ids:
        try:
            (username, repo_name, repo_path) = prepare_repo(idx, clone=True)
            branch = GitManager.get_default_branch(repo_path)
            if not branch:
                print(f"Failed to get default branch for repo: {repo_path}")    
            else:
                analyzer = RepoDataAnalyzer(username, repo_name, repo_path, branch)
                sorted_commits: list[tuple[str, datetime]]  = analyzer.all_commits
                
                sorted_commits_serializable = [
                    (commit_hash, commit_dt.isoformat() if isinstance(commit_dt, datetime) else commit_dt)
                    for commit_hash, commit_dt in sorted_commits
                ]
                
                full_repo_name = f"{repo_name}@{username}"
                data[full_repo_name] = sorted_commits_serializable
        except Exception as e:
            print(e)
            traceback.print_exc()
        finally:
            flush_repo(idx)
    
    FileUtils.save_json_file(data_output_path, data)
    print(f"Data saved to {data_output_path}")
    
if __name__ == "__main__":
    collect_repo_hashes()