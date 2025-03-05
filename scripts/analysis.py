import os
import argparse
from concurrent.futures import ProcessPoolExecutor
from corpus import prepare_corpus, flush_repo
from data_analyzer import RepoDataAnalyzer
from corpus_analyzer import CorpusAnalyzer
from utils import GitManager, ColoredStr
import traceback

def analyze_repo_data(idx):
    """
    Analyzes the collected data for a given repository.
    """
    try:
        (username, repo_name, repo_path) = prepare_corpus(idx, clone=True)
        branch = GitManager.get_default_branch(repo_path)
        if not branch:
            print(ColoredStr.red(f"Failed to get default branch for repo: {repo_path}"))
        else:
            try:        
                print(f"\n {ColoredStr.cyan('Analyzing repo data...')}\n[{idx}] Repo: {ColoredStr.blue(repo_path)} | Branch: {ColoredStr.green(branch)}")
                analyzer = RepoDataAnalyzer(username, repo_name, repo_path, branch)
                analyzer.setup_repo_dataset(idx, username, repo_name)
                analyzer.load_raw_smells()
                analyzer.calculate_smells_lifespan()
                analyzer.load_raw_refactorings()
                analyzer.map_refactorings_to_smells()
                analyzer.save_data_to_json(username, repo_name)
            except Exception as e:
                print(ColoredStr.red(e))
                traceback.print_exc()
            finally:
                analyzer.flush_repo_dataset()
    except Exception as e:
        print(ColoredStr.red(e))
        traceback.print_exc()
    finally:
        flush_repo(idx)
        
def analyze_corpus_data():
    try:
        print(f"\n {ColoredStr.cyan('Analyzing corpus data...')}")
        analyzer = CorpusAnalyzer()
        analyzer.process()
        
        # OLD CODE
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
    idxs = [0, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 23, 24, 25, 26, 27, 28, 29, 99, 103, 109, 111]
    # # idxs = [18] # for manual testing
    
    # for idx in idxs:
    #     (username, repo_name, repo_path) = prepare_corpus(idx, clone=False)
        
    #     default_branch = GitManager.get_default_branch(repo_path)
    #     if not default_branch:
    #         print(ColoredStr.red(f"Failed to get default branch for repo: {repo_path}"))
    #     else:
    #         analyze_repo_data(idx, username, repo_name, repo_path, branch=default_branch)
    
    # tasks = []
    # with ProcessPoolExecutor(max_workers=4) as executor:
    #     for idx in idxs:
    #         tasks.append(executor.submit(analyze_repo_data, idx))
                
    #     # Wait for all tasks to complete
    #     for task in tasks:
    #         task.result()
    # print("All repositories data analyzed parallelly.")
        
    analyze_corpus_data()
    