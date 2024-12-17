import os
import config
from runners import Designite, RefMiner
from data_analyzer import RepoDataAnalyzer
from lifespan_analyzer import LifespanAnalyzer
from utils import GitManager, load_json_file, ColoredStr


def analyze_repo(repo_path, default_branch):
    # Generate code smells
    try:
        designite_runner = Designite()
        designite_runner.analyze_commits(repo_path, branch=default_branch)
    except Exception as e:
        print(ColoredStr.red(e))
    
    # Generate refactoring data
    try:
        ref_miner_runner = RefMiner()
        ref_miner_runner.analyze(repo_path, branch=default_branch)
    except Exception as e:
        print(ColoredStr.red(e))
        
def analyze_repo_data(repo_path, branch):
    try:
        print(f"\nRepo: {ColoredStr.blue(repo_path)} | Branch: {ColoredStr.green(branch)}")
        repo_data_analyzer = RepoDataAnalyzer(repo_path, branch)
        repo_data_analyzer.calculate_smells_lifespan()
        repo_data_analyzer.calc_smell_range()
        repo_data_analyzer.map_refactorings_to_smells()
        repo_data_analyzer.save_lifespan_to_json()
    except Exception as e:
        print(ColoredStr.red(e))
        
def analyze_corpus_data():
    try:
        lifespan_analyzer = LifespanAnalyzer()
        avg_commit_spans, avg_days_spans, avg_smells_span, top_k_ref_4_smells = lifespan_analyzer.process_repos()
        # lifespan_analyzer.plot_avg_lifespan(avg_commit_spans, avg_days_spans)
        lifespan_analyzer.plot_avg_smell_lifespan(avg_smells_span)
        lifespan_analyzer.plot_top_k_ref_4_smell(top_k_ref_4_smells)
    except Exception as e:
        print(ColoredStr.red(e))

repos = [
    # "AgriCraft",
    # 'AnaMuslim', *~
    # "auth0-spring-security5-api-sample", *~
    # "Chisels-and-Bits", *~
    # "cthul" *~
    # "heraj",
    # "Dungeon",
    # "sx4"
]
    

if __name__ == "__main__":
    # for repo in repos:
    #     CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    #     TARGET_REPO_PATH = os.path.join(config.REPOS_PATH, repo)
    #     REPOS_LIST: dict = load_json_file(config.REPO_LIST_PATH)
    #     REPOS_DATA: dict = {}
        
    #     # try:
    #     #     for repo in REPOS_DATA.get("items")[:1]:
    #     #         username, repo_name = repo.get("name").split("/")
    #     #         GitManager.clone_repo(
    #     #             repo_path=os.path.join(config.REPOS_PATH, username, repo_name),
    #     #             repo_full_name=repo.get("name")
    #     #         )
                    
    #     # except Exception as e:
    #     #     print(e)
            
    #     default_branch = GitManager.get_default_branch(TARGET_REPO_PATH)
    #     if not default_branch:
    #         print(ColoredStr.red(f"Failed to get default branch for repo: {TARGET_REPO_PATH}"))
    #         continue
        
    #     analyze_repo(repo_path=TARGET_REPO_PATH, default_branch=default_branch)
    #     analyze_repo_data(repo_path=TARGET_REPO_PATH, branch=default_branch)
        
    analyze_corpus_data()
    