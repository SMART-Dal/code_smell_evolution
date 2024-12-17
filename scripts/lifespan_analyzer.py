import os
import config
from utils import traverse_directory, load_json_file, get_smell_dict
import matplotlib.pyplot as plt
import numpy as np

class LifespanAnalyzer:
    def __init__(self):
        self.lib_path = config.SMELLS_LIB_PATH
        self.plots_dir = os.path.join(config.OUTPUT_PATH, 'plots') 

    def process_repos(self):
        avg_commit_spans = {}
        avg_days_spans = {}
        avg_smells_spans = {}
        top_refactorings = {}
        
        for file_path in traverse_directory(self.lib_path):
            if file_path.endswith('.json'):
                repo_name = os.path.basename(file_path).replace('.json', '')
                repo_data = load_json_file(file_path)
                avg_commit_span, avg_days_span, avg_smells_span, ref_occurances = self.calculate_avg_spans(repo_data)
                avg_commit_spans[repo_name] = avg_commit_span
                avg_days_spans[repo_name] = avg_days_span
                
                for smell, span in avg_smells_span.items():
                    if smell in avg_smells_spans:
                        avg_smells_spans[smell]["commit_span"].append(span["avg_commit_span"])
                        avg_smells_spans[smell]["days_span"].append(span["avg_days_span"])
                    else:
                        avg_smells_spans[smell] = {
                            "commit_span": [span["avg_commit_span"]],
                            "days_span": [span["avg_days_span"]]
                        }
                
                for smell, ref_types in ref_occurances.items():
                    if smell not in top_refactorings:
                        top_refactorings[smell] = {}
                    for ref_type, count in ref_types.items():
                        if ref_type in top_refactorings[smell]:
                            top_refactorings[smell][ref_type] += count
                        else:
                            top_refactorings[smell][ref_type] = count
        
        # Calculate average smells span for the entire corpus
        corpus_avg_smells_span = {}
        for smell, spans in avg_smells_spans.items():
            avg_commit_span = sum(spans["commit_span"]) / len(spans["commit_span"]) if spans["commit_span"] else 0
            avg_days_span = sum(spans["days_span"]) / len(spans["days_span"]) if spans["days_span"] else 0
            corpus_avg_smells_span[smell] = {
                "avg_commit_span": avg_commit_span,
                "avg_days_span": avg_days_span
            }
        
        top_k = 5
        # Calculate top k refactorings for each smell
        top_k_refactorings = {}
        for smell, ref_types in top_refactorings.items():
            sorted_ref_types = sorted(ref_types.items(), key=lambda item: item[1], reverse=True)
            top_k_refactorings[smell] = sorted_ref_types[:top_k]
        
        return avg_commit_spans, avg_days_spans, corpus_avg_smells_span, top_k_refactorings
    
    def calculate_avg_spans(self, repo_data: dict):
        commit_spans = []
        days_spans = []
        smells_span = {}
        ref_count = 0
        
        # Initialize smells_span with default values
        for smell_name in config.SMELL_COL_NAMES:
            smells_span[smell_name] = {"commit_span": [], "days_span": [], "refactoring_types": []}
        
        for smell, data in repo_data.items():
            smell_dict = get_smell_dict(smell)
            smell_name = next((k for k in smell_dict.keys() if k in config.SMELL_COL_NAMES), None)
            
            commit_spans.append(data.get('commit_span', 0))
            days_spans.append(data.get('days_span', 0))

            if smell_name:
                smells_span[smell_name]["commit_span"].append(data.get('commit_span', 0))
                smells_span[smell_name]["days_span"].append(data.get('days_span', 0))
                
                for refactorings in data.get('mapped_refactorings', []):
                    ref_type = refactorings.get('type', None)
                    ref_count += 1
                    
                    if ref_type:
                        smells_span[smell_name]["refactoring_types"].append(ref_type)
        
        avg_commit_span = sum(commit_spans) / len(commit_spans) if commit_spans else 0
        avg_days_span = sum(days_spans) / len(days_spans) if days_spans else 0
        refactoring_type_cooccurrence = {}
        
        
        avg_smells_span = {}
        for smell_name, spans in smells_span.items():
            avg_commit_span = sum(spans["commit_span"]) / len(spans["commit_span"]) if spans["commit_span"] else 0
            avg_days_span = sum(spans["days_span"]) / len(spans["days_span"]) if spans["days_span"] else 0
            avg_smells_span[smell_name] = {
                "avg_commit_span": avg_commit_span,
                "avg_days_span": avg_days_span
            }
            refactoring_type_cooccurrence[smell_name] = {}
            for ref_type in spans["refactoring_types"]:
                if ref_type in refactoring_type_cooccurrence[smell_name]:
                    refactoring_type_cooccurrence[smell_name][ref_type] += 1
                else:
                    refactoring_type_cooccurrence[smell_name][ref_type] = 1
        
        print(f"Total Refactorings: {ref_count}")
        return avg_commit_span, avg_days_span, avg_smells_span, refactoring_type_cooccurrence

    def plot_avg_lifespan(self, avg_commit_spans, avg_days_spans):
        repos = list(avg_commit_spans.keys())
        avg_commits = list(avg_commit_spans.values())
        avg_days = list(avg_days_spans.values())

        plt.figure(figsize=(12, 6))

        # Plot Commit Span
        plt.subplot(1, 2, 1)
        plt.bar(repos, avg_commits, color='skyblue')
        plt.xlabel('Repositories')
        plt.ylabel('Average Commit Span')
        plt.title('Average Commit Span per Repository')
        plt.xticks(rotation=45, ha='right')

        # Plot Days Span
        plt.subplot(1, 2, 2)
        plt.bar(repos, avg_days, color='orange')
        plt.xlabel('Repositories')
        plt.ylabel('Average Days Span')
        plt.title('Average Days Span per Repository')
        plt.xticks(rotation=45, ha='right')

        # plt.tight_layout()
        # plt.show()
        plt.savefig(os.path.join(self.plots_dir, 'avg_lifespan.png'), dpi=300, bbox_inches='tight')
    
    def plot_avg_smell_lifespan(self, avg_smells_span ):
        categories = list(avg_smells_span.keys())
        avg_commit_spans = [avg_smells_span[smell]['avg_commit_span'] for smell in categories]
        avg_days_spans = [avg_smells_span[smell]['avg_days_span'] for smell in categories]
        
        # Set up bar chart positions
        x = np.arange(len(categories))  # the label locations
        width = 0.35  # the width of the bars

        # Create the plot
        fig, ax = plt.subplots(figsize=(10, 6))
        bars1 = ax.bar(x - width/2, avg_commit_spans, width, label='Avg Commit Span', color='skyblue')
        bars2 = ax.bar(x + width/2, avg_days_spans, width, label='Avg Days Span', color='lightgreen')

        # Add labels, title, and legend
        ax.set_xlabel('Smell Category')
        ax.set_ylabel('Average Span')
        ax.set_title('Average Commit and Days Span for Each Smell Category')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend()

        # Annotate bars with values
        for bar in bars1 + bars2:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')
            
        plt.savefig(os.path.join(self.plots_dir, 'avg_smell_lifespan.png'), dpi=300, bbox_inches='tight')
        
    def plot_top_k_ref_4_smell(self, smell_data):
        categories = list(smell_data.keys())
        methods = {method for smell in smell_data.values() for method, _ in smell}
        methods = sorted(methods)  # Keep order consistent

        # Build matrix for plotting
        data_matrix = []
        for category in categories:
            data = dict(smell_data[category])
            data_matrix.append([data.get(method, 0) for method in methods])

        # Transpose data for bar plotting
        data_matrix = np.array(data_matrix).T

        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(len(categories))
        bar_width = 0.15
        colors = plt.cm.tab10.colors

        for i, method in enumerate(methods):
            ax.bar(x + i * bar_width, data_matrix[i], bar_width, label=method, color=colors[i % len(colors)])

        # Formatting
        ax.set_title('Top Refactorings for Each Smell Category', fontsize=14)
        ax.set_xlabel('Smell Categories', fontsize=12)
        ax.set_ylabel('Count', fontsize=12)
        ax.set_xticks(x + bar_width * (len(methods) - 1) / 2)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend(title="Refactoring Methods", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

        plt.savefig(os.path.join(self.plots_dir, 'top_k_ref_with_smell.png'), dpi=300, bbox_inches='tight')