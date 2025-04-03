import os
import re
import random
import config
from utils import FileUtils

class SampleGenerator:
    def __init__(self):
        self.lib_dir = config.SMELL_REF_MAP_PATH
        self.corpus = []
        
    def build_samples(self):
        for file_path in FileUtils.traverse_directory(self.lib_dir):
            file_path: str
            if file_path.endswith('.json') and not file_path.endswith('.stats.json'):
                repo_full_name = os.path.basename(file_path).replace('.json', '')
                repo_data = FileUtils.load_json_file(file_path)
                metadata = repo_data.get("metadata", {})
                smell_instances = repo_data.get("smell_instances", [])
                
                for smell_instance in smell_instances:
                    smell_instance: dict
                    del smell_instance["introduced_by_refactorings"]
                    smell_instance = {
                        "repo_full_name": repo_full_name,
                        "branch": metadata.get("branch", ""),
                        "is_the_map_correct?": False,
                        "reason_for_incorrect_mapping?": "",
                        **smell_instance
                    }
                    self.corpus.append(smell_instance)
                    
    def get_grouped_by(self, smell_kind, smell_name, refactoring_type):
        grouped = []
        for sample in self.corpus:
            default_v = sample.get("smell_versions", {})[0]
            if default_v["smell_kind"] == smell_kind and default_v["smell_name"] == smell_name:
                for ref in sample["removed_by_refactorings"]:
                    if ref["type_name"] == refactoring_type:
                        clean_sample = self._clean_sample(sample, refactoring_type)
                        grouped.append(clean_sample)
        
        return grouped
    
    def _clean_sample(self, sample, refactoring_type):
        sample = sample.copy()
        sample["removed_by_refactorings"] = [
            ref for ref in sample["removed_by_refactorings"] if ref["type_name"] == refactoring_type
        ]
        return sample
        
    def get_top_k_pairs(self):
        stats_file_path = os.path.join(self.lib_dir, '_TOP_K_CORPUS.stats.json')
        if not os.path.exists(stats_file_path):
            print(f"Stats file not found: {stats_file_path}")
            return
        
        stats_data = FileUtils.load_json_file(stats_file_path)
        
        removed_by_refactorings_count = stats_data.get("removed_by_refactorings_count", {})
        return removed_by_refactorings_count
    
    def pick_random_samples(self, random_seed, num_samples):
        top_k_pairs = self.get_top_k_pairs()
        if not top_k_pairs:
            print("No top K pairs found.")
            return []

        
        flatten_pairs = {}
        for smell_kind, smells in top_k_pairs.items():
            for smell_name, refactors in smells.items():
                for refactor_type, count in refactors.items():
                    if refactor_type == "other":
                        continue  # Ignore "other" category

                    limit = min(count, num_samples)  # Restrict selection per type
                    key = (smell_kind, smell_name, refactor_type)
                    flatten_pairs[key] = limit

        selected_samples = {}
        
        for pair, limit in flatten_pairs.items():
            smell_kind, smell_name, refactor_type = pair
            grouped_samples = self.get_grouped_by(smell_kind, smell_name, refactor_type)
            if limit > len(grouped_samples):
                print(f"Warning: Limit {limit} exceeds the number of samples for {pair}")
                limit = len(grouped_samples)
            
            random.seed(random_seed)
            selected_samples[pair] = random.sample(grouped_samples, limit)
            
        return selected_samples

    def save_samples_to_json(self, samples, authors=2):
        output_dir = config.MANUAL_ANALYSIS_PATH
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for pair, samples in samples.items():
            smell_kind, smell_name, refactor_type = pair
            chunk_size = max(1, len(samples) // authors)
            
            for idx in range(authors):
                start = idx * chunk_size
                end = start + chunk_size
                author_samples = samples[start:end]
                
                if not author_samples:
                    continue
                
                output_file_path = os.path.join(output_dir, f'auth_{(idx+1)}_{smell_kind}_{smell_name}_{refactor_type}.json')
                
                FileUtils.save_json_file(output_file_path, author_samples)
                
    def group_observations(self):
        top_k_pairs = self.get_top_k_pairs()
        output_dir = config.MANUAL_ANALYSIS_PATH
        grouped = []
        for file_path in FileUtils.traverse_directory(output_dir):
            file_path: str
            file_name = os.path.basename(file_path)
            if file_path.endswith('.json') and file_name.startswith('auth_1_'):
                name_without_ext = file_name.rsplit('.', 1)[0]
                parts = re.split(r'_', name_without_ext, maxsplit=2)
                
                info_from_file_name = parts[2].split('_', maxsplit=2)
                
                file_data = FileUtils.load_json_file(file_path)
                
                correct_map = 0
                incorrect_map = 0
                reasons = []
                for item in file_data:
                    if item["is_the_map_correct?"]:
                        correct_map += 1
                    else:
                        incorrect_map += 1
                    
                    if item["reason_for_incorrect_mapping?"] not in reasons and item["reason_for_incorrect_mapping?"] != "":
                        reasons.append(item["reason_for_incorrect_mapping?"])
                
                group = {
                    "smell_kind": info_from_file_name[0],
                    "smell_name": info_from_file_name[1],
                    "refactor_type": info_from_file_name[2],
                    "correct_map": correct_map*2,
                    "incorrect_map": incorrect_map*2,
                    "reasons": reasons
                }
                occurance = top_k_pairs.get(group["smell_kind"], {}).get(group["smell_name"], {}).get(group["refactor_type"], "NA")
                group["occurance"] = occurance
                
                
                grouped.append(group)
                
        # Divide the list into two parts by kind
        kind_a = [item for item in grouped if item["smell_kind"] == "Design"]
        kind_b = [item for item in grouped if item["smell_kind"] == "Implementation"]

        # Sort each part by smell_name
        kind_a_sorted = sorted(kind_a, key=lambda x: x["smell_name"])
        kind_b_sorted = sorted(kind_b, key=lambda x: x["smell_name"])

        # Combine the sorted lists
        sorted_grouped = kind_a_sorted + kind_b_sorted
        
        # latex generation
        pass
        
        print("\n\nTABLE\n\n")
        print("Smell Name, Refactor Type, Occurence")
        for group in sorted_grouped:
            smell_name = group["smell_name"]
            ref_type = group["refactor_type"]
            occurence = group["occurance"]
            print(f"{smell_name}, {ref_type}, {occurence}")

        # for latex table generation
        # smells_order = []
        # ref_order = []
        # pairs = {}
        # for group in sorted_grouped:
        #     if group["smell_name"] not in pairs:
        #         pairs[group["smell_name"]] = []
        #         if group["smell_name"] not in smells_order:
        #             smells_order.append(group["smell_name"])
        #     pairs[group["smell_name"]].append((group["refactor_type"], group["occurance"]))
        #     if group["refactor_type"] not in ref_order:
        #         ref_order.append((group["refactor_type"], group["occurance"]))
        
        # print(f"Total smells: {len(smells_order)}")
        # smell_command_dict = {}
        # for smell_name in smells_order:
        #     cleaned_smell_name = smell_name.replace(' ', '').replace('-', '')
        #     caps_command_name = f"\\smell{cleaned_smell_name}"
        #     smell_command_dict[smell_name] = caps_command_name
        #     print(f"\\newcommand{{{caps_command_name}}}{{\srtype{{{smell_name}}}}}")
        #     small_caps_command_name = f"\\smell{cleaned_smell_name.lower()}"
        #     print(f"\\newcommand{{{small_caps_command_name}}}{{\srtype{{{smell_name.lower()}}}}}")
            
        # ref_command_dict = {}
        # print(f"\nTotal refs: {len(ref_order)}")
        # for ref, _ in ref_order:
        #     caps_command_name = f"\\ref{ref.replace(' ', '')}"
        #     print(f"\\newcommand{{{caps_command_name}}}{{\srtype{{{ref}}}}}")
        #     ref_command_dict[ref] = caps_command_name
        #     small_caps_command_name = f"\\ref{ref.replace(' ', '').lower()}"
        #     print(f"\\newcommand{{{small_caps_command_name}}}{{\srtype{{{ref.lower()}}}}}")
        
        # print("\n\nTABLE\n\n")
        # # for smell_name, refactorings in pairs.items():
        # #     smell_order_id = smells_order.index(smell_name)+1
        # #     print_line = f"s\\textsubscript{{{smell_order_id}}}[{smell_name}]  &   "
        # #     for ref in refactorings:
        # #         print_line += f"r\\textsubscript{{{ref_order.index(ref)+1}}}[{ref}], " if ref != refactorings[-1] else f"r\\textsubscript{{{ref_order.index(ref)+1}}}[{ref}]"
        # #     # ref_order_ids = [ref_order.index(ref) for ref in refactorings]
        # #     # print(f"S{smell_order_id}[{smell_name}] & {', '.join([f'R{ref_order.index(ref)}[{ref}]' for ref in refactorings])} \\\\")
        # #     print(print_line + "    \\\\")
        
        # for smell_name, refactorings in pairs.items():
        #     print_line = f"{smell_command_dict[smell_name]} & "
        #     for i, (ref, occ) in enumerate(refactorings):
        #         ref_line = f"{ref_command_dict[ref]}({occ})"
        #         if i < len(refactorings) - 1:
        #             print_line += f"{ref_line}, "
        #         else:
        #             print_line += f"{ref_line}"
        #     print(print_line + " \\\\")

        # Save the sorted observations to a JSON file
        # output_file_path = os.path.join(output_dir, 'observations.json')
        # FileUtils.save_json_file(output_file_path, sorted_grouped)
                    
if __name__ == "__main__":
    sample_generator = SampleGenerator()
    # sample_generator.build_samples()
    # print(f"Total samples: {len(sample_generator.corpus)}")
    # final_samples = sample_generator.pick_random_samples(random_seed=42, num_samples=12)
    # print(f"No. of sample groups: {len(final_samples)}")
    # sample_generator.save_samples_to_json(final_samples)
    sample_generator.group_observations()