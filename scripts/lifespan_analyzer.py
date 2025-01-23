import os
import config
from utils import FileUtils
import matplotlib.pyplot as plt
import numpy as np
from models import CorpusMetrics

class CorpusLifespanAnalyzer:
    def __init__(self):
        self.lib_path = config.SMELL_LIFESPANS_PATH
        self.plots_dir = os.path.join(config.OUTPUT_PATH, 'plots')
        if not os.path.exists(self.plots_dir):
            os.makedirs(self.plots_dir)
        
        self.active_smell_groups = {}
        self.corpus_metric = CorpusMetrics()

    def process_corpus(self):
        
        for file_path in FileUtils.traverse_directory(self.lib_path):
            file_path: str
            if file_path.endswith('.json') and not file_path.endswith('_stats.json'):
                repo_full_name = os.path.basename(file_path).replace('.json', '')
                repo_data = FileUtils.load_json_file(file_path)
            
                avg_commit_span, avg_days_span, smell_metrics = self.generate_repo_metrics(repo_data)
                self.corpus_metric.add_repo_avg_commit_span(repo_full_name, avg_commit_span)
                self.corpus_metric.add_repo_avg_days_span(repo_full_name, avg_days_span)
                
                for smell, metrics in smell_metrics.items():
                    self.corpus_metric.add_smell_avg_commit_span(smell, metrics["avg_commit_span"])
                    self.corpus_metric.add_smell_avg_days_span(smell, metrics["avg_days_span"])
                    
                    for ref_type, count in metrics["ref_type_occurance"].items():
                        self.corpus_metric.add_smell_ref_count(smell, ref_type, count)
        
        # Calculate average smells span for the entire corpus
        corpus_avg_smell_metrics = {}
        top_k_ref = 6
        corpus_top_ref_per_smell = {}
        for smell, metrics in self.corpus_metric.smell_metrics.items():
            corpus_avg_commit_span = self.list_avg(metrics["avg_commit_span"])
            corpus_avg_days_span = self.list_avg(metrics["avg_days_span"])
            corpus_avg_smell_metrics[smell] = {
            "avg_commit_span": corpus_avg_commit_span,
            "avg_days_span": corpus_avg_days_span
            }
            
            # Calculate top 5 refactorings for each smell
            ref_counts = metrics.get("ref_count", {})
            sorted_ref_counts = sorted(ref_counts.items(), key=lambda item: item[1], reverse=True)
            corpus_top_ref_per_smell[smell] = sorted_ref_counts[:top_k_ref]
            
        # Save the corpus stats to a JSON file
        corpus_stats = {
            "avg_smell_metrics": corpus_avg_smell_metrics,
            "top_ref_per_smell": corpus_top_ref_per_smell
        }
        FileUtils.save_json_file(os.path.join(self.lib_path, '_corpus_stats.json'), corpus_stats)
        
        return corpus_avg_smell_metrics, corpus_top_ref_per_smell
    
    def generate_repo_metrics(self, repo_data):
        metadata: dict = repo_data.get('metadata', None)
        smell_instances: list = repo_data.get('smell_instances', [])
        
        repo_stats_filename = None
        repo_commit_span_list = []
        repo_days_span_list = []
        repo_smells_span_info: dict[str, dict] = {}
        
        path = metadata.get('path', None)
        if not path:
            print("Path not found in metadata to generate stats json")
            return 0, 0, {}, {}
        else:
            parts = path.split('/')
            repo_stats_filename = f"{parts[-1]}@{parts[-2]}_stats.json"
        
        # Initialize smells_span with default values
        smell_types: dict = metadata.get('smell_types', None)
        if not smell_types:
            print("Smell Types not found in metadata")
            return 0, 0, {}, {}
        else:
            for smell_type, smell_names in smell_types.items():
                for smell_name in smell_names: 
                    self._track_smell_groups(smell_type, smell_name)
                    repo_smells_span_info[smell_name] = {
                        "smell_type": smell_type,
                        "commit_span": [],
                        "days_span": [],
                        "refactoring_types": [],
                        "refactoring_type_count": {}
                    }
        
        # Collect span data for each smell
        for smell_instance in smell_instances:
            smell_instance: dict
            smell_info = smell_instance.get('smell', None)
            
            commit_span = smell_instance.get('commit_span', 0)
            days_span = smell_instance.get('days_span', 0)
            
            if commit_span is not None:
                repo_commit_span_list.append(commit_span)
            if days_span is not None:
                repo_days_span_list.append(days_span)

            if smell_info:
                smell_name = smell_info.get('smell_name', None)
                if commit_span is not None:
                    repo_smells_span_info[smell_name]["commit_span"].append(commit_span)
                if days_span is not None:
                    repo_smells_span_info[smell_name]["days_span"].append(days_span)
                
                for refactoring in smell_instance.get('removed_by_refactorings', []):
                    ref_type = refactoring.get('type_name', None)
                    
                    if ref_type:
                        repo_smells_span_info[smell_name]["refactoring_types"].append(ref_type)
                        if ref_type in repo_smells_span_info[smell_name]["refactoring_type_count"]:
                            repo_smells_span_info[smell_name]["refactoring_type_count"][ref_type] += 1
                        else:
                            repo_smells_span_info[smell_name]["refactoring_type_count"][ref_type] = 1
        
        repo_avg_commit_span = self.list_avg(repo_commit_span_list)
        repo_avg_days_span = self.list_avg(repo_days_span_list)
        
        repo_smells_metrics = {}
        for smell_name, smell_metrics in repo_smells_span_info.items():
            avg_commit_span = self.list_avg(smell_metrics["commit_span"])
            avg_days_span = self.list_avg(smell_metrics["days_span"])
            ref_type_occurances = smell_metrics["refactoring_type_count"]
            repo_smells_metrics[smell_name] = {
                "avg_commit_span": avg_commit_span,
                "avg_days_span": avg_days_span,
                "ref_type_occurance": ref_type_occurances
            }
            
        # Save the repo stats to a JSON file
        repo_stats = {
            "avg_commit_span": repo_avg_commit_span,
            "avg_days_span": repo_avg_days_span,
            "smells_metrics": repo_smells_metrics
        }
        FileUtils.save_json_file(os.path.join(self.lib_path, repo_stats_filename), repo_stats)
        
        return repo_avg_commit_span, repo_avg_days_span, repo_smells_metrics
    
    def list_avg(self, list_of_ints: list[int]) -> float:
        # Filter out non-numeric values and ensure the list contains only valid numbers
        valid_numbers = [x for x in list_of_ints if isinstance(x, (int, float))]
        
        # Calculate the average only if the list has valid numbers
        return sum(valid_numbers) / len(valid_numbers) if valid_numbers else 0

    def _track_smell_groups(self, smell_type, smell_name):
        if smell_type not in self.active_smell_groups:
            self.active_smell_groups[smell_type] = []
        if smell_name not in self.active_smell_groups[smell_type]:
            self.active_smell_groups[smell_type].append(smell_name)

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
    
    def plot_avg_smell_lifespan(self, avg_smells_span, smell_groups):
        for smell_type, smells in smell_groups.items():
            # Filter data for the current smell type
            categories = [smell for smell in smells if smell in avg_smells_span]
            avg_commit_spans = [avg_smells_span[smell]['avg_commit_span'] for smell in categories]
            avg_days_spans = [avg_smells_span[smell]['avg_days_span'] for smell in categories]
            
            if not categories:
                print(f"No data available for {smell_type}. Skipping plot.")
                continue
            
            # Set up bar chart positions
            x = np.arange(len(categories))  # the label locations
            width = 0.35  # the width of the bars

            # Create the plot
            fig, ax = plt.subplots(figsize=(10, 6))
            bars1 = ax.bar(x - width / 2, avg_commit_spans, width, label='Avg Commit Span', color='skyblue')
            bars2 = ax.bar(x + width / 2, avg_days_spans, width, label='Avg Days Span', color='lightgreen')

            # Add labels, title, and legend
            ax.set_xlabel('Smell Category')
            ax.set_ylabel('Average Span')
            ax.set_title(f'Average Commit and Days Span for {smell_type}')
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

            # Save the plot
            filename = f'avg_smell_lifespan_{smell_type.replace(" ", "_").lower()}.png'
            plt.savefig(os.path.join(self.plots_dir, filename), dpi=300, bbox_inches='tight')
            plt.close(fig)  # Close the figure to free memory
        
    def plot_avg_smell_lifespan_combined(self, avg_smells_span, smell_groups):
        # Aggregate data for top-level smell types
        top_level_categories = []
        combined_commit_spans = []
        combined_days_spans = []

        for smell_type, smells in smell_groups.items():
            # Filter data for child smells
            categories = [smell for smell in smells if smell in avg_smells_span]
            avg_commit_spans = [avg_smells_span[smell]['avg_commit_span'] for smell in categories]
            avg_days_spans = [avg_smells_span[smell]['avg_days_span'] for smell in categories]

            if not categories:
                print(f"No data available for {smell_type}. Skipping aggregation.")
                continue

            # Aggregate stats for the current smell type
            top_level_categories.append(smell_type)
            combined_commit_spans.append(np.mean(avg_commit_spans))
            combined_days_spans.append(np.mean(avg_days_spans))

        if not top_level_categories:
            print("No data available for any smell type. Skipping top-level plot.")
            return

        # Set up bar chart positions
        x = np.arange(len(top_level_categories))  # the label locations
        width = 0.35  # the width of the bars

        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 8))
        bars1 = ax.bar(x - width / 2, combined_commit_spans, width, label='Avg Commit Span', color='skyblue')
        bars2 = ax.bar(x + width / 2, combined_days_spans, width, label='Avg Days Span', color='lightgreen')

        # Add labels, title, and legend
        ax.set_xlabel('Smell Type')
        ax.set_ylabel('Average Span')
        ax.set_title('Average Commit and Days Span by Smell Type')
        ax.set_xticks(x)
        ax.set_xticklabels(top_level_categories, rotation=45, ha='right')
        ax.legend()

        # Annotate bars with values
        for bar in bars1 + bars2:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')

        # Save the plot
        filename = 'avg_smell_lifespan_COMBINED.png'
        plt.savefig(os.path.join(self.plots_dir, filename), dpi=300, bbox_inches='tight')
        plt.close(fig)  # Close the figure to free memory        

    def plot_top_k_ref_4_smell(self, smell_data, smell_groups):
        for smell_type, smells in smell_groups.items():
            # Filter data for the current smell type
            categories = [smell for smell in smells if smell in smell_data]
            if not categories:
                print(f"No data available for {smell_type}. Skipping plot.")
                continue

            methods = {method for smell in categories for method, _ in smell_data[smell]}
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
            ax.set_title(f'Top Refactorings for {smell_type}', fontsize=14)
            ax.set_xlabel('Smell Categories', fontsize=12)
            ax.set_ylabel('Count', fontsize=12)
            ax.set_xticks(x + bar_width * (len(methods) - 1) / 2)
            ax.set_xticklabels(categories, rotation=45, ha='right')
            ax.legend(title="Refactoring Methods", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
            ax.grid(axis='y', linestyle='--', alpha=0.7)

            # Save the plot
            filename = f'top_k_ref_with_smell_{smell_type.replace(" ", "_").lower()}.png'
            plt.savefig(os.path.join(self.plots_dir, filename), dpi=300, bbox_inches='tight')
            plt.close(fig)  # Close the figure to free memory
            
    def plot_top_k_ref_4_smell_combined(self, smell_data, smell_groups):
        # Aggregate data for top-level smell types
        top_level_categories = []
        method_names = set()

        # Collect data for each smell type
        aggregated_data = {}
        for smell_type, smells in smell_groups.items():
            categories = [smell for smell in smells if smell in smell_data]
            if not categories:
                print(f"No data available for {smell_type}. Skipping aggregation.")
                continue

            top_level_categories.append(smell_type)
            aggregated_data[smell_type] = {}

            for category in categories:
                for method, count in smell_data[category]:
                    if method not in aggregated_data[smell_type]:
                        aggregated_data[smell_type][method] = []
                    aggregated_data[smell_type][method].append(count)
                    method_names.add(method)

        if not top_level_categories:
            print("No data available for any smell type. Skipping top-level plot.")
            return

        # Sort methods and prepare the data matrix
        method_names = sorted(method_names)
        data_matrix = []

        for smell_type in top_level_categories:
            method_counts = []
            for method in method_names:
                # Average counts for the current smell type and method
                counts = aggregated_data[smell_type].get(method, [])
                method_counts.append(np.mean(counts) if counts else 0)
            data_matrix.append(method_counts)

        data_matrix = np.array(data_matrix).T  # Transpose for bar plotting

        # Plot
        fig, ax = plt.subplots(figsize=(12, 8))
        x = np.arange(len(top_level_categories))
        bar_width = 0.15
        colors = plt.cm.tab10.colors

        for i, method in enumerate(method_names):
            ax.bar(x + i * bar_width, data_matrix[i], bar_width, label=method, color=colors[i % len(colors)])

        # Formatting
        ax.set_title('Top Refactorings Combined by Smell Type', fontsize=14)
        ax.set_xlabel('Smell Types', fontsize=12)
        ax.set_ylabel('Count', fontsize=12)
        ax.set_xticks(x + bar_width * (len(method_names) - 1) / 2)
        ax.set_xticklabels(top_level_categories, rotation=45, ha='right')
        ax.legend(title="Refactoring Methods", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

        # Save the plot
        filename = 'top_k_ref_COMBINED.png'
        plt.savefig(os.path.join(self.plots_dir, filename), dpi=300, bbox_inches='tight')
        plt.close(fig)  # Close the figure to free memory
            
    def pieplot_top_k_ref_4_smell(self, smell_data, smell_groups): 
        for smell_type, smells in smell_groups.items():
            # Filter data for the current smell type
            categories = [smell for smell in smells if smell in smell_data]
            if not categories:
                print(f"No data available for {smell_type}. Skipping plot.")
                continue

            skipped_smells = []  # Keep track of skipped smells
            valid_smells = []  # Keep track of valid smells for plotting

            for smell_name in categories:
                if not smell_data.get(smell_name, []):
                    skipped_smells.append(smell_name)
                else:
                    valid_smells.append(smell_name)

            if not valid_smells:
                print(f"No valid smells with data found for {smell_type}. Skipping plot.")
                continue

            # Determine the number of subplots (one for each valid smell)
            num_smells = len(valid_smells)
            cols = 2  # Number of columns for subplots
            rows = (num_smells + cols - 1) // cols  # Calculate rows needed

            # Create a figure with subplots
            fig, axes = plt.subplots(rows, cols, figsize=(12, 6 * rows))
            axes = axes.flatten()  # Flatten the 2D array of axes for easy indexing

            for i, smell_name in enumerate(valid_smells):
                ax = axes[i]  # Select the appropriate subplot axis
                # Get the method counts for the current smell_name
                method_counts = dict(smell_data[smell_name])

                # Prepare data for the pie chart
                methods = list(method_counts.keys())
                counts = list(method_counts.values())
                total = sum(counts)
                percentages = [count / total * 100 for count in counts]

                # Create the pie chart
                wedges, texts, autotexts = ax.pie(
                    counts,
                    labels=methods,
                    autopct=lambda pct: f'{pct:.1f}%\n({int(pct * total / 100)})',
                    colors=plt.cm.tab10.colors[:len(methods)],
                    startangle=140,
                    textprops={'fontsize': 8}
                )

                # Formatting
                ax.set_title(f'{smell_name}', fontsize=12)

            # Remove empty subplots if any
            for j in range(i + 1, len(axes)):
                fig.delaxes(axes[j])

            # Overall title for the smell type
            fig.suptitle(f'Top Refactorings for {smell_type}', fontsize=16)
            fig.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout

            # Save the plot
            filename = f'pie_charts_{smell_type.replace(" ", "_").lower()}.png'
            plt.savefig(os.path.join(self.plots_dir, filename), dpi=300, bbox_inches='tight')
            plt.close(fig)  # Close the figure to free memory

            # Log skipped smells
            if skipped_smells:
                print(f"Skipped the following smells for {smell_type} due to no data: {', '.join(filter(None, skipped_smells))}")