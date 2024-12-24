import os
import config
from corpus import prepare_corpus, prepare_from_corpus_info
from runners import Designite, RefMiner
from data_analyzer import RepoDataAnalyzer
from lifespan_analyzer import LifespanAnalyzer
from utils import GitManager, ColoredStr


def execute_designite(username, repo_name, repo_path, branch):
    """
    Collects code smells for a given repository. 
    """
    # Generate code smells
    try:
        designite_runner = Designite()
        designite_runner.analyze_commits(username, repo_name, repo_path, branch)
    except Exception as e:
        print(ColoredStr.red(e))

def execute_refminer(username, repo_name, repo_path, branch):
    """
    Collects refactorings for a given repository.
    """
    try:
        ref_miner_runner = RefMiner()
        ref_miner_runner.analyze(username, repo_name, repo_path, branch)
    except Exception as e:
        print(ColoredStr.red(e))
        
def analyze_repo_data(username, repo_name, repo_path, branch):
    """
    Analyzes the collected data for a given repository.
    """
    try:
        print(f"\nRepo: {ColoredStr.blue(repo_path)} | Branch: {ColoredStr.green(branch)}")
        repo_data_analyzer = RepoDataAnalyzer(username, repo_name, repo_path, branch)
        repo_data_analyzer.calculate_smells_lifespan()
        repo_data_analyzer.map_refactorings_to_smells()
        repo_data_analyzer.save_lifespan_to_json(username, repo_name)
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

if __name__ == "__main__":
    CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    
    corpus_info: dict = prepare_corpus()
    
    for username, repos in corpus_info.items():
        for repo in repos:
            TARGET_REPO_PATH = os.path.join(config.CORPUS_PATH, username, repo)
                
            default_branch = GitManager.get_default_branch(TARGET_REPO_PATH)
            if not default_branch:
                print(ColoredStr.red(f"Failed to get default branch for repo: {TARGET_REPO_PATH}"))
                continue
            
            execute_designite(username, repo, TARGET_REPO_PATH, branch=default_branch)
            execute_refminer(username, repo, TARGET_REPO_PATH, branch=default_branch)
            
            analyze_repo_data(username, repo, TARGET_REPO_PATH, branch=default_branch)
        
    # analyze_corpus_data()
    