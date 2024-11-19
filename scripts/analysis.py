from runners import Designite, RefMiner
from utils import get_git_branches
import os
import config

repos = [
    "AgriCraft",
    "auth0-spring-security5-api-sample"
]

if __name__ == "__main__":
    CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    TARGET_REPO_PATH = os.path.join(config.REPOS_PATH, repos[1])
    
    branches = get_git_branches(TARGET_REPO_PATH)
    default_branch = branches[0]
    
    try:
        Designite().analyze_commits(repo_path = TARGET_REPO_PATH, branch = default_branch)
    except Exception as e:
        print(e)
    
    try:
        ref_miner_runner = RefMiner().analyze(repo_path = TARGET_REPO_PATH, output_path = config.OUTPUT_PATH)
    except Exception as e:
        print(e)