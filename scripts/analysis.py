import os
from corpus import prepare_corpus, prepare_from_corpus_info
from data_analyzer import RepoDataAnalyzer
from lifespan_analyzer import CorpusLifespanAnalyzer
from utils import GitManager, ColoredStr
import traceback
   
def analyze_repo_data(username, repo_name, repo_path, branch):
    """
    Analyzes the collected data for a given repository.
    """
    try:
        print(f"\nRepo: {ColoredStr.blue(repo_path)} | Branch: {ColoredStr.green(branch)}")
        repo_data_analyzer = RepoDataAnalyzer(username, repo_name, repo_path, branch)
        repo_data_analyzer.calculate_smells_lifespan()
        repo_data_analyzer.map_refactorings_to_smells()
        repo_data_analyzer.generate_metadata()
        repo_data_analyzer.save_lifespan_to_json(username, repo_name)
    except Exception as e:
        print(ColoredStr.red(e))
        traceback.print_exc()
        
def analyze_corpus_data():
    try:
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
    # corpus_generator = prepare_corpus(REPO_IDX, clone=False)
    corpus_generator = [
        ('bitwig', 'bitwig-extensions', os.path.join(config.CORPUS_PATH, 'bitwig', 'bitwig-extensions')),
        ('cgerard321', 'champlain_petclinic', os.path.join(config.CORPUS_PATH, 'cgerard321', 'champlain_petclinic')),
        ('fabricmc', 'mixin', os.path.join(config.CORPUS_PATH, 'fabricmc', 'mixin')),
        ('falsehoodmc', 'fabrication', os.path.join(config.CORPUS_PATH, 'falsehoodmc', 'fabrication')),
        ('linlinjava', 'litemall', os.path.join(config.CORPUS_PATH, 'linlinjava', 'litemall')),
        ('mapbox', 'mapbox-java', os.path.join(config.CORPUS_PATH, 'mapbox', 'mapbox-java')),
        ('marvionkirito', 'altoclef', os.path.join(config.CORPUS_PATH, 'marvionkirito', 'altoclef')),
        ('reneargento', 'algorithms-sedgewick-wayne', os.path.join(config.CORPUS_PATH, 'reneargento', 'algorithms-sedgewick-wayne')),
        ('serg-delft', 'andy', os.path.join(config.CORPUS_PATH, 'serg-delft', 'andy')),
        ('skbkontur', 'extern-java-sdk', os.path.join(config.CORPUS_PATH, 'skbkontur', 'extern-java-sdk')),
        ('sublinks', 'sublinks-api', os.path.join(config.CORPUS_PATH, 'sublinks', 'sublinks-api')),
        ('thombergs', 'code-examples', os.path.join(config.CORPUS_PATH, 'thombergs', 'code-examples')),
        ('warmuuh', 'milkman', os.path.join(config.CORPUS_PATH, 'warmuuh', 'milkman')),
    ]
    
    # for username, repo_name, repo_path in corpus_generator:
    #     default_branch = GitManager.get_default_branch(repo_path)
    #     if not default_branch:
    #         print(ColoredStr.red(f"Failed to get default branch for repo: {repo_path}"))
    #         continue
        
    #     analyze_repo_data(username, repo_name, repo_path, branch=default_branch)
        
    analyze_corpus_data()
    