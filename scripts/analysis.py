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
                analyzer.commits_analysis()
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
    except Exception as e:
        print(ColoredStr.red(e))
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run analysis on repo index or entire corpus")
    parser.add_argument("idx", type=int, nargs="?", help="index of the repository to process. If not provided, corpus analysis will be performed.")
    args = parser.parse_args()
    
    if args.idx is not None:
        analyze_repo_data(args.idx)
    else:
        analyze_corpus_data()
    