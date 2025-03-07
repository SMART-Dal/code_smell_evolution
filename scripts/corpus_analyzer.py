import os
import config
import pandas as pd
import seaborn as sns
from pprint import pprint
import matplotlib.pyplot as plt
from utils import FileUtils
from models import DESIGN_SMELL, IMP_SMELL
# from mlxtend.frequent_patterns import apriori, association_rules
# from mlxtend.preprocessing import TransactionEncoder

class CorpusAnalyzer:
    def __init__(self):
        self.lib_dir = config.SMELL_REF_MAP_PATH
        self.plots_dir = config.PLOTS_PATH
        if not os.path.exists(self.plots_dir):
            os.makedirs(self.plots_dir)
        
        self.corpus_stats = {}
        self.top_k_corpus_stats = {}
        self.sankey_plot_data = {
            DESIGN_SMELL: {},
            IMP_SMELL: {},
            "refactorings_count": {}, # will always link to removed smells (never to alive ones)
            "no_refactoring": 0
        }
        self.lifespan_plot_data = []
        self.transactions = []
        
        self._ref_type_counts = {
            DESIGN_SMELL: {},
            IMP_SMELL: {}
        }
        self._smell_types = {
            DESIGN_SMELL: [],
            IMP_SMELL: [],
            f"TOTAL_ALIVE_{DESIGN_SMELL}": 0,
            f"TOTAL_ALIVE_{IMP_SMELL}": 0,
            f"TOTAL_REMOVED_{DESIGN_SMELL}": 0,
            f"TOTAL_REMOVED_{IMP_SMELL}": 0,
        }
            
    def process(self):
        for file_path in FileUtils.traverse_directory(self.lib_dir):
            file_path: str
            if file_path.endswith('.json') and not file_path.endswith('.stats.json'):
                repo_full_name = os.path.basename(file_path).replace('.json', '')
                repo_data = FileUtils.load_json_file(file_path)
                # repo_data_smell_instances = repo_data.get("smell_instances", [])
                
                self.calculate_repo_stats(file_path, repo_full_name, repo_data)

        self.top_k_pairs()
        # self.save_corpus_stats()
        
        # self.generate_sankey_plot()
        # self.plot_lifespan()
        # self.perform_apriori_analysis()
        for kind, ref_type_counts in self._ref_type_counts.items():
            sorted_ref_type_counts = dict(sorted(ref_type_counts.items(), key=lambda item: item[1], reverse=True))
            print(f"Refactoring counts for {kind}:")
            print(f"TOTAL_ALIVE_{kind}: {self._smell_types[f'TOTAL_ALIVE_{kind}']}")
            print(f"TOTAL_REMOVED_{kind}: {self._smell_types[f'TOTAL_REMOVED_{kind}']}")
            print(f"Smell types: {self._smell_types[kind]}\n")
            pprint(sorted_ref_type_counts, sort_dicts=False)
            print("\n")
            
    def calculate_repo_stats(self, repo_data_path, repo_name, repo_data):
        """
        Calculate smell instance statistics.
        """
        smell_instance_pairs = repo_data.get("smell_instances", [])
        map_stats = {
            "detected_design_smells": 0,
            "detected_imp_smells": 0,
            "deteced_refactorings": 0,
            "total_smell_instances": len(smell_instance_pairs),
            "moved_smells": 0,
            "resolved_smells": 0,
            "unresolved_smells": 0,
            "never_introduced_by_refactorings": 0,
            "never_resolved_by_refactorings": 0,
            "introduced_by_refactorings_count": {
                DESIGN_SMELL: {},
                IMP_SMELL: {}},
            "removed_by_refactorings_count": {
                DESIGN_SMELL: {},
                IMP_SMELL: {}
            }
        }
        
        for smell_instance in smell_instance_pairs:
            is_smell_instance_alive = smell_instance.get("is_alive", False)
            if len(smell_instance["smell_versions"]) > 1:
                map_stats["moved_smells"] += 1
            smell_kind = smell_instance["smell_versions"][0]["smell_kind"]
            smell_type = smell_instance["smell_versions"][0]["smell_name"]
            if smell_type not in self.sankey_plot_data[smell_kind]:
                self.sankey_plot_data[smell_kind][smell_type] = {"alive_smells": 0, "removed_smells": 0}
                
            if is_smell_instance_alive:
                self._smell_types[f"TOTAL_ALIVE_{smell_kind}"] += 1
            else:
                self._smell_types[f"TOTAL_REMOVED_{smell_kind}"] += 1
                
            if smell_type not in self._smell_types[smell_kind]:
                self._smell_types[smell_kind].append(smell_type)
            
            
            introduced_by_refactorings = smell_instance.get("introduced_by_refactorings", [])
            if len(introduced_by_refactorings) == 0:
                map_stats["never_introduced_by_refactorings"] += 1
            refs_count_introduced = self.get_refactorings_stats(introduced_by_refactorings, mode='introduced', smell_kind=smell_kind)
            self._update_refactoring_counts(map_stats["introduced_by_refactorings_count"], smell_kind, smell_type, refs_count_introduced)
            
            if is_smell_instance_alive:
                map_stats["unresolved_smells"] += 1
                self.sankey_plot_data[smell_kind][smell_type]["alive_smells"] += 1
            else:
                map_stats["resolved_smells"] += 1
                self.sankey_plot_data[smell_kind][smell_type]["removed_smells"] += 1
                self.add_transaction(smell_instance)
                
                removed_by_refactorings = smell_instance.get("removed_by_refactorings", [])
                if len(removed_by_refactorings) == 0:
                    map_stats["never_resolved_by_refactorings"] += 1
                refs_count_removed = self.get_refactorings_stats(removed_by_refactorings, mode='removed', smell_kind=smell_kind)
                self._update_refactoring_counts(map_stats["removed_by_refactorings_count"], smell_kind, smell_type, refs_count_removed)
                
                commit_span = smell_instance.get("commit_span", 0)
                self.lifespan_plot_data.append({
                    'repo_name': repo_name,
                    'smell_kind': smell_kind,
                    'smell_type': smell_type,
                    'commit_span': commit_span
                })

        (D, I, R) = self._add_stats('map_stats', map_stats, repo_data_path)
        map_stats["detected_design_smells"] = D
        map_stats["detected_imp_smells"] = I
        map_stats["deteced_refactorings"] = R
        
        self.add_to_corpus_stats(map_stats)

    def add_to_corpus_stats(self, map_stats):
        """
        Merge the current repo stats into the overall corpus stats.
        """
        for key, value in map_stats.items():
            if key not in self.corpus_stats:
                self.corpus_stats[key] = value
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in self.corpus_stats[key]:
                        self.corpus_stats[key][sub_key] = sub_value
                    elif isinstance(sub_value, dict):
                        for sub_sub_key, sub_sub_value in sub_value.items():
                            if sub_sub_key not in self.corpus_stats[key][sub_key]:
                                self.corpus_stats[key][sub_key][sub_sub_key] = sub_sub_value
                            else:
                                self.corpus_stats[key][sub_key][sub_sub_key] = self._merge_dicts(self.corpus_stats[key][sub_key][sub_sub_key], sub_sub_value)
                    else:
                        self.corpus_stats[key][sub_key] += sub_value
            else:
                self.corpus_stats[key] += value

    def _merge_dicts(self, dict1, dict2):
        """
        Merge two dictionaries, adding values of common keys.
        """
        for key, value in dict2.items():
            if key in dict1:
                if isinstance(value, dict):
                    dict1[key] = self._merge_dicts(dict1[key], value)
                else:
                    dict1[key] += value
            else:
                dict1[key] = value
        return dict1
        
    def get_refactorings_stats(self, refs_list, mode, smell_kind=None):
        """
        Calculate refactoring statistics.
        """
        refs_count = {}
        
        if len(refs_list) == 0:
            self.sankey_plot_data["no_refactoring"] += 1
        
        for ref in refs_list:
            type_name = ref.get("type_name")
            
            if mode == 'removed':
                if type_name not in self._ref_type_counts[smell_kind]:
                    self._ref_type_counts[smell_kind][type_name] = 0
                self._ref_type_counts[smell_kind][type_name] += 1
                
                if type_name not in self.sankey_plot_data["refactorings_count"]:
                    self.sankey_plot_data["refactorings_count"][type_name] = 0
                self.sankey_plot_data["refactorings_count"][type_name] += 1
            
            if type_name in refs_count:
                refs_count[type_name] += 1
            else:
                refs_count[type_name] = 1
        return refs_count
    
    def _update_refactoring_counts(self, stats_dict, smell_kind, smell_type, refs_count):
        """
        Update the refactoring counts for a given smell kind and type.
        """
        if smell_kind not in stats_dict:
            stats_dict[smell_kind] = {}
        if smell_type not in stats_dict[smell_kind]:
            stats_dict[smell_kind][smell_type] = {}
        
        for ref_type, count in refs_count.items():
            if ref_type in stats_dict[smell_kind][smell_type]:
                stats_dict[smell_kind][smell_type][ref_type] += count
            else:
                stats_dict[smell_kind][smell_type][ref_type] = count
    
    def _add_stats(self, new_data_key, new_data_dict, file_path):
        stats_file_path = file_path.replace('.json', '.stats.json')
        if os.path.exists(stats_file_path):
            stats_data = FileUtils.load_json_file(stats_file_path)
        else:
            stats_data = {}
        # Designite stats of repo
        total_d_smells = stats_data["designite_stats"]["smells_collected"]["total_design_smells"]
        total_i_smells = stats_data["designite_stats"]["smells_collected"]["total_imp_smells"]
        # RefMiner stats of repo
        total_refactorings = stats_data["refminer_stats"]["total_refactorings"]
        
        new_data_dict["detected_design_smells"] = total_d_smells
        new_data_dict["detected_imp_smells"] = total_i_smells
        new_data_dict["deteced_refactorings"] = total_refactorings
        
        # Insert the new data at the top of the existing data
        updated_stats_data = {new_data_key: new_data_dict}
        if new_data_key in stats_data:
            del stats_data[new_data_key]
        updated_stats_data.update(stats_data)
        
        FileUtils.save_json_file(stats_file_path, updated_stats_data)
        return total_d_smells, total_i_smells, total_refactorings
    
    def generate_sankey_plot(self):
        # for smell_kind, smell_ref_dict in data["removed_by_refactorings_count"].items():
        #     introduced_lines = ["//introduced pairs"]
        #     for smell_type, ref_counts in smell_ref_dict.items():
        #         other_count = ref_counts.pop('other', None)
        #         for ref_type, count in ref_counts.items():
        #             introduced_lines.append(f"{ref_type} [{count}] {smell_type}")
        #         if other_count is not None:
        #             introduced_lines.append(f"other [{other_count}] {smell_type}")
            
        #     removed_lines = ["//removed pairs"]
        #     for smell_type, ref_counts in data["removed_by_refactorings_count"][smell_kind].items():
        #         other_count = ref_counts.pop('other', None)
        #         for ref_type, count in ref_counts.items():
        #             removed_lines.append(f"{smell_type} [{count}] {ref_type}\\n")
        #         if other_count is not None:
        #             removed_lines.append(f"{smell_type} [{other_count}] other\\n")
        
        def is_ref_type_in_top_k(self, smell_kind, target_ref_type):
            found = False
            for _, smell_ref_count in self.top_k_corpus_stats["removed_by_refactorings_count"][smell_kind].items():
                if target_ref_type in smell_ref_count:
                    found = True
                    break
            return found
        
        for smell_kind in [DESIGN_SMELL, IMP_SMELL]:
            plot_data = "//smells\n"
            for smell_type, smell_status in self.sankey_plot_data[smell_kind].items():
                alive_count = smell_status["alive_smells"]
                removed_count = smell_status["removed_smells"]
                plot_data += f"{smell_type} [{alive_count}] Alive smells\n"
                plot_data += f"{smell_type} [{removed_count}] Removed smells\n"
                
            plot_data += "//refactorings\n"
            for ref_type, count in self.sankey_plot_data["refactorings_count"].items():
                
                if is_ref_type_in_top_k(self, smell_kind, ref_type):
                    plot_data += f"Removed smells [{count}] {ref_type}\n"
                else:
                    plot_data += f"Removed smells [{count}] other\n"
            plot_data += f"Removed smells [{self.sankey_plot_data['no_refactoring']}] No Refactoring\n"
                
            
            output_file = os.path.join(self.plots_dir, f'sankey_data_{smell_kind}.txt')
            with open(output_file, 'w') as f:
                f.write(plot_data)
            print(f"Sankey data for {smell_kind} saved to {output_file}")
            
    # def add_transaction(self, smell_instance):
    #     """
    #     Add a smell instance to the apriori analysis dataframe.
    #     """
    #     if len(smell_instance["removed_by_refactorings"]) == 0:
    #         return
    #     smell_type = smell_instance["smell_versions"][0]["smell_name"]
    #     refactoring_types = [ref["type_name"] for ref in smell_instance.get("removed_by_refactorings", [])]
        
    #     # Append the new row to the apriori analysis dataframe
    #     self.transactions.append([smell_type] + refactoring_types)
    
    # def perform_apriori_analysis(self):
    #     """
    #     Perform apriori analysis on the transactions to find frequent itemsets.
    #     """
    #     if not self.transactions:
    #         print("No data available for analysis.")
    #         return
    #     else:
    #         print(f"Total transactions: {len(self.transactions)}")
            
        
    #     # Prepare the data for apriori algorithm
    #     te = TransactionEncoder()
    #     te_ary = te.fit(self.transactions).transform(self.transactions)
    #     df = pd.DataFrame(te_ary, columns=te.columns_)

    #     # Apply the apriori algorithm
    #     frequent_itemsets = apriori(df, min_support=0.01, use_colnames=True)
    #     if frequent_itemsets.empty:
    #         print("No frequent itemsets found.")
    #         return
        
    #     # Generate association rules
    #     rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.1)
    #     if rules.empty:
    #         print("No association rules found.")
    #         return
        
    #     # Print the rules
    #     print("Association rules:")
    #     pprint(rules)
        
    #     # Save the rules to a file
    #     rules_path = os.path.join(self.plots_dir, 'apriori_rules.csv')
    #     rules.to_csv(rules_path, index=False)
    #     print(f"Apriori rules saved to {rules_path}")
        
        
    def plot_lifespan(self):
        """
        Plot the lifespan of smell instances with high-quality pixel density using boxen plot.
        """
        df = pd.DataFrame(self.lifespan_plot_data)
        
        # Remove outliers based on commit_span with a looser threshold
        Q1 = df['commit_span'].quantile(0.25)
        Q3 = df['commit_span'].quantile(0.75)
        IQR = Q3 - Q1
        df = df[(df['commit_span'] >= (Q1 - 1.5 * IQR)) & (df['commit_span'] <= (Q3 + 1.5 * IQR))]
        
        # Create different plots for different smell kinds
        for smell_kind in df['smell_kind'].unique():
            plt.figure(figsize=(14, 8), dpi=300)  # Set dpi for high-quality plot
            sns.boxenplot(data=df[df['smell_kind'] == smell_kind], 
                          x='smell_type', y='commit_span', 
                          orient='v',
                          palette='husl', hue='smell_type')

            # Customize the plot
            plt.xlabel('Smell Name', fontsize=14)
            plt.ylabel('Commit Span', fontsize=14)
            plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better readability
            plt.ylim(bottom=0)  # Set the lower limit of y-axis to 0 to avoid negative values

            # Save the plot to the plots directory
            plot_path = os.path.join(self.plots_dir, f'commit_span_boxenplot_{smell_kind}_QUANTILED.png')
            plt.tight_layout()
            plt.savefig(plot_path, dpi=300)  # Save with high dpi for better quality
            plt.close()

            print(f"Boxen plot for {smell_kind} saved to {plot_path}")

    def top_k_pairs(self, k=5):
        def get_top_k_with_other(ref_counts: dict, k):
            sorted_items = sorted(ref_counts.copy().items(), key=lambda item: item[1], reverse=True)
            top_k_items = dict(sorted_items[:k])
            if len(sorted_items) > k:
                other_sum = sum(count for _, count in sorted_items[k:])
                top_k_items['other'] = other_sum
            return top_k_items

        self.top_k_corpus_stats["introduced_by_refactorings_count"] = {}
        for smell_kind, smell_ref_dict in self.corpus_stats["introduced_by_refactorings_count"].items():
            self.top_k_corpus_stats["introduced_by_refactorings_count"][smell_kind] = {}
            for smell_type, ref_counts in smell_ref_dict.items():
                self.top_k_corpus_stats["introduced_by_refactorings_count"][smell_kind][smell_type] = get_top_k_with_other(ref_counts, k)

        self.top_k_corpus_stats["removed_by_refactorings_count"] = {}
        for smell_kind, smell_ref_dict in self.corpus_stats["removed_by_refactorings_count"].items():
            self.top_k_corpus_stats["removed_by_refactorings_count"][smell_kind] = {}
            for smell_type, ref_counts in smell_ref_dict.items():
                self.top_k_corpus_stats["removed_by_refactorings_count"][smell_kind][smell_type] = get_top_k_with_other(ref_counts, k)
                
    def save_corpus_stats(self):
        """
        Save the calculated statistics for the corpus.
        """
        corpus_stats_path = os.path.join(self.lib_dir, '_CORPUS.stats.json')
        FileUtils.save_json_file(corpus_stats_path, self.corpus_stats)
        top_k_corpus_stats_path = os.path.join(self.lib_dir, '_TOP_K_CORPUS.stats.json')
        FileUtils.save_json_file(top_k_corpus_stats_path, self.top_k_corpus_stats)
        print(f"Corpus statistics saved to {corpus_stats_path}")