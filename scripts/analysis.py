import os
from corpus import prepare_corpus
from data_analyzer import RepoDataAnalyzer
from lifespan_analyzer import CorpusLifespanAnalyzer
from utils import GitManager, ColoredStr
import traceback

def analyze_repo_data(idx, username, repo_name, repo_path, branch):
    """
    Analyzes the collected data for a given repository.
    """
    try:
        print(f"\n {ColoredStr.cyan('Analyzing repo data...')}\n[{idx}] Repo: {ColoredStr.blue(repo_path)} | Branch: {ColoredStr.green(branch)}")
        repo_data_analyzer = RepoDataAnalyzer(username, repo_name, repo_path, branch)
        repo_data_analyzer.setup_repo_dataset(idx, username, repo_name)
        repo_data_analyzer.load_raw_smells()
        repo_data_analyzer.calculate_smells_lifespan()
        repo_data_analyzer.load_raw_refactorings()
        repo_data_analyzer.map_refactorings_to_smells()
        repo_data_analyzer.calculate_lifespan_stats()
        repo_data_analyzer.save_data_to_json(username, repo_name)
    except Exception as e:
        print(ColoredStr.red(e))
        traceback.print_exc()
    finally:
        repo_data_analyzer.flush_repo_dataset()
        
def analyze_corpus_data():
    try:
        print(f"\n {ColoredStr.cyan('Analyzing corpus data...')}")
        lifespan_analyzer = CorpusLifespanAnalyzer()
        avg_smells_span, top_k_ref_4_smells = lifespan_analyzer.process_corpus()
        smell_groups = lifespan_analyzer.active_smell_groups
        # lifespan_analyzer.plot_avg_lifespan(avg_commit_spans, avg_days_spans)
        lifespan_analyzer.plot_avg_smell_lifespan(avg_smells_span, smell_groups)
        lifespan_analyzer.plot_avg_smell_lifespan_combined(avg_smells_span, smell_groups)
        lifespan_analyzer.plot_top_k_ref_4_smell(top_k_ref_4_smells, smell_groups)
        lifespan_analyzer.plot_top_k_ref_4_smell_combined(top_k_ref_4_smells, smell_groups)
        lifespan_analyzer.pieplot_top_k_ref_4_smell(top_k_ref_4_smells, smell_groups)
        
    except Exception as e:
        print(ColoredStr.red(e))
        traceback.print_exc()

if __name__ == "__main__":
    CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    # idxs = [0, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 23]
    idxs = [18] # for manual testing
    
    for idx in idxs:
        (username, repo_name, repo_path) = prepare_corpus(idx, clone=False)
        
        default_branch = GitManager.get_default_branch(repo_path)
        if not default_branch:
            print(ColoredStr.red(f"Failed to get default branch for repo: {repo_path}"))
        else:
            analyze_repo_data(idx, username, repo_name, repo_path, branch=default_branch)
        
    # analyze_corpus_data()
    