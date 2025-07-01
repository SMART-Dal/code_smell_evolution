import os
import traceback
from datetime import datetime
import config
from utils import FileUtils

def collect_repo_hashes():
    data = {}
    data_output_path = os.path.join(config.BIN_PATH, "data", "corpus_commits.json")
    
    map_stats = [
        file_path for file_path in FileUtils.traverse_directory(config.SMELL_REF_MAP_PATH) if file_path.endswith('.stats.json') 
    ]
    
    print(f"Found {len(map_stats)} map stats to process.")
    
    for f in map_stats:
        try:
            map_data = FileUtils.load_json_file(f)
            repo_full_name = os.path.basename(f).replace('.stats.json', '')
            sorted_commits: list[tuple[str, datetime]] = map_data.get("repo_commits", [])
            
            sorted_commits_serializable = [
                (commit_hash, commit_dt.isoformat() if isinstance(commit_dt, datetime) else commit_dt)
                for commit_hash, commit_dt in sorted_commits
            ]
            
            data[repo_full_name] = sorted_commits_serializable
        except Exception as e:
            print(f"Error processing {f}: {e}")
            traceback.print_exc()
    
    FileUtils.save_json_file(data_output_path, data)
    print(f"Data saved to {data_output_path}")
    
if __name__ == "__main__":
    collect_repo_hashes()