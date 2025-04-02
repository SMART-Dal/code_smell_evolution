import argparse
from corpus import prepare_repo, flush_repo
from data_analyzer import RepoDataAnalyzer
from corpus_analyzer import CorpusAnalyzer
from utils import GitManager, ColoredStr
import traceback

def analyze_repo_data(idx):
    """
    Analyzes the collected data for a given repository.
    """
    try:
        (username, repo_name, repo_path) = prepare_repo(idx, clone=True)
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
        analyzer.load_corpus()
        # analyzer.generate_top_k_plots()
        # analyzer.total_commits_analyzed()
        # analyzer.process_unmapped_refactorigns()
        # analyzer.process_unmapped_smells()
    except Exception as e:
        print(ColoredStr.red(e))
        traceback.print_exc()

if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Run analysis on repo index")
    # parser.add_argument("idx", type=int, help="index of the repository to process.")
    # args = parser.parse_args()
    
    # analyze_repo_data(args.idx)
        
    analyze_corpus_data()
    