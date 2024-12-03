import os
import config
from runners import Designite, RefMiner
from data_analyzer import RepoDataAnalyzer
from utils import GitManager, load_json_file

repos = [
    "AgriCraft",
    "auth0-spring-security5-api-sample"
]

if __name__ == "__main__":
    CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    TARGET_REPO_PATH = os.path.join(config.REPOS_PATH, repos[1])
    REPOS_LIST: dict = load_json_file(config.REPO_LIST_PATH)
    REPOS_DATA: dict = {}
    
    # try:
    #     for repo in REPOS_DATA.get("items")[:1]:
    #         username, repo_name = repo.get("name").split("/")
    #         GitManager.clone_repo(
    #             repo_path=os.path.join(config.REPOS_PATH, username, repo_name),
    #             repo_full_name=repo.get("name")
    #         )
                
    # except Exception as e:
    #     print(e)
        
    branches = GitManager.get_git_branches(TARGET_REPO_PATH)
    default_branch = branches[0]
    
    try:
        designite_runner = Designite()
        designite_runner.analyze_commits(repo_path = TARGET_REPO_PATH, branch = default_branch)
    except Exception as e:
        print(e)
    
    try:
        ref_miner_runner = RefMiner().analyze(repo_path = TARGET_REPO_PATH, output_path = config.OUTPUT_PATH)
    except Exception as e:
        print(e)
    
    try:
        repo_data_analyzer = RepoDataAnalyzer(
            repo_path =TARGET_REPO_PATH,
            branch = default_branch
        )
        repo_data_analyzer.calculate_smells_lifespan()
        repo_data_analyzer.map_refactorings_to_smells()
        repo_data_analyzer.generate_function_info()
        repo_data_analyzer.save_lifespan_to_json()
    except Exception as e:
        print(e)
    