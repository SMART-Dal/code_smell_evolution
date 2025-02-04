import os
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
                        grouped.append(sample)
        
        return grouped
        
    def get_top_k_pairs(self):
        stats_file_path = os.path.join(self.lib_dir, '_TOP_K_CORPUS.stats.json')
        if not os.path.exists(stats_file_path):
            print(f"Stats file not found: {stats_file_path}")
            return
        
        stats_data = FileUtils.load_json_file(stats_file_path)
        
        removed_by_refactorings_count = stats_data.get("removed_by_refactorings_count", {})
        return removed_by_refactorings_count
    
    def pick_random_samples(self, num_samples):
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
                    
if __name__ == "__main__":
    sample_generator = SampleGenerator()
    sample_generator.build_samples()
    print(f"Total samples: {len(sample_generator.corpus)}")
    final_samples = sample_generator.pick_random_samples(num_samples=50)
    print(f"Selected samples: {len(final_samples)}")
    sample_generator.save_samples_to_json(final_samples)