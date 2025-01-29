import os
import argparse
from corpus import prepare_corpus
from data_analyzer import RepoDataAnalyzer
from corpus_analyzer import CorpusAnalyzer
from utils import GitManager, ColoredStr
import traceback

def analyze_repo_data(idx, username, repo_name, repo_path, branch):
    """
    Analyzes the collected data for a given repository.
    """
    try:
        print(f"\n {ColoredStr.cyan('Analyzing repo data...')}\n[{idx}] Repo: {ColoredStr.blue(repo_path)} | Branch: {ColoredStr.green(branch)}")
        analyzer = RepoDataAnalyzer(username, repo_name, repo_path, branch)
        analyzer.setup_repo_dataset(idx, username, repo_name)
        analyzer.load_raw_smells()
        analyzer.calculate_smells_lifespan()
        analyzer.load_raw_refactorings()
        analyzer.map_refactorings_to_smells()
        analyzer.calculate_lifespan_stats()
        analyzer.save_data_to_json(username, repo_name)
    except Exception as e:
        print(ColoredStr.red(e))
        traceback.print_exc()
    finally:
        analyzer.flush_repo_dataset()
        
def analyze_corpus_data():
    try:
        print(f"\n {ColoredStr.cyan('Analyzing corpus data...')}")
        analyzer = CorpusAnalyzer()
        analyzer.process()
        # avg_smells_span, top_k_ref_4_smells = analyzer.process_corpus()
        # smell_groups = analyzer.active_smell_groups
        # # analyzer.plot_avg_lifespan(avg_commit_spans, avg_days_spans)
        # analyzer.plot_avg_smell_lifespan(avg_smells_span, smell_groups)
        # analyzer.plot_avg_smell_lifespan_combined(avg_smells_span, smell_groups)
        # analyzer.plot_top_k_ref_4_smell(top_k_ref_4_smells, smell_groups)
        # analyzer.plot_top_k_ref_4_smell_combined(top_k_ref_4_smells, smell_groups)
        # analyzer.pieplot_top_k_ref_4_smell(top_k_ref_4_smells, smell_groups)
        
    except Exception as e:
        print(ColoredStr.red(e))
        traceback.print_exc()

if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Run analysis on repo index")
    # parser.add_argument("idx", type=int, help="index of the repository to process.")
    # args = parser.parse_args()
    
    # CURR_DIR = os.path.dirname(os.path.realpath(__file__))
    # # idxs = [22, 24, 25, 26, 27, 29, 31, 32, 33, 34, 35, 36, 37, 39]
    # # idxs = [18] # for manual testing
    
    # # for idx in idxs:
    # (username, repo_name, repo_path) = prepare_corpus(args.idx, clone=False)
    
    # default_branch = GitManager.get_default_branch(repo_path)
    # if not default_branch:
    #     print(ColoredStr.red(f"Failed to get default branch for repo: {repo_path}"))
    # else:
    #     analyze_repo_data(args.idx, username, repo_name, repo_path, branch=default_branch)
        
    analyze_corpus_data()
    