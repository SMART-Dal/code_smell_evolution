import os
import random
import config
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from utils import FileUtils
from corpus_analyzer import DF_COLS

class SampleGenerator:
    def __init__(self):
        self.lib_dir = config.SMELL_REF_MAP_PATH
        self.top_k = pd.DataFrame(columns=["smell_type", "removal_refactorings", "count"])
        
    
    def load_corpus(self):
        df = pd.DataFrame(columns=DF_COLS)
        corpus_bin = os.path.join(self.lib_dir, "corpus.csv")
        if os.path.exists(corpus_bin):
            df = pd.read_csv(corpus_bin, low_memory=False)
            print(f"Loaded corpus with {len(df)} records.")
            print(f"Shape: {df.shape}")
            print(df.head())
            return df
        else:
            raise FileNotFoundError(f"Corpus file not found: {corpus_bin}")
        
    def top_k_pairs(self, k=5):
        corpus_df = self.load_corpus()
        # Remove extra spaces and split the 'removal_refactorings' by ';'
        corpus_df['removal_refactorings'] = corpus_df['removal_refactorings'].fillna('').apply(lambda x: [r.strip() for r in x.split(';') if r.strip()])

        # Explode the DataFrame to have one row per smell-refactoring pair
        exploded_df = corpus_df.explode('removal_refactorings')
        
        # Group by smell_type and individual refactoring, and count
        refactoring_counts = exploded_df.groupby(['smell_type', 'removal_refactorings']).size().reset_index(name='count')
        
        # Get top 5 refactorings for each smell_type
        top_refactorings = (
            refactoring_counts
            .sort_values(['smell_type', 'count'], ascending=[True, False])
            .groupby('smell_type')
            .head(k)
        )

        # Save the result to a CSV file
        output_file = os.path.join(self.lib_dir, 'top_5_pairs.csv')
        self.top_k = top_refactorings
        self.top_k.to_csv(output_file, index=False)
        print(f"Top {k} pairs saved to {output_file}")
    
    def generate_analysis_samples(self):
        
        top_k_pairs = {}
        for _, row in self.top_k.iterrows():
            if row['smell_type'] not in top_k_pairs:
                top_k_pairs[row['smell_type']] = []
            if row['removal_refactorings'] not in top_k_pairs[row['smell_type']]:
                top_k_pairs[row['smell_type']].append(row['removal_refactorings'])

        all_samples = self.get_all_samples(top_k_pairs)
        
        for smell_type, refactoring_types in top_k_pairs.items():
            for ref in refactoring_types:
                samples_subset = all_samples.get(f"{smell_type}_{ref}", [])
                picked_samples = self.pick_random_samples(smell_type, ref, samples_subset)
                
                updated_samples = []
                for s in picked_samples:
                    s: dict
                    updated_sample = {
                        "human_analysis": {
                            "correct_mapping?": False,
                            "decreases_severity?": False,
                            "reason?": ""
                        },
                        "llm_analysis": {
                            "correct_mapping?": False,
                            "decreases_severity?": False,
                            "reason?": ""
                        },
                        **s
                    }
                    updated_samples.append(updated_sample)
                
                self.save_samples_to_json(updated_samples, smell_type, ref)
    
    def get_all_samples(self, top_k_pairs):
        all_samples = {}
        paths = list(FileUtils.traverse_directory(self.lib_dir))
        for file_path in random.sample(paths, len(paths)):
            file_path: str
            if file_path.endswith('.json') and not file_path.endswith('.stats.json') and not file_path.endswith('.chain.json'):
                repo_full_name = os.path.basename(file_path).replace('.json', '')
                map_data = FileUtils.load_json_file(file_path)
                metadata = map_data.get("metadata", {})
                map_chain_data = FileUtils.load_json_file(file_path.replace('.json', '.chain.json'))
                smell_instances = map_data.get("smell_instances", [])
                
                for c in map_chain_data:
                    c: dict
                    
                    latest_chain_item = c.get("chain")[-1]
                    si = self._get_smell_instance(smell_instances, latest_chain_item)
                    if si["is_alive"]:
                        continue
                    si_smell_type = si["smell_versions"][-1]["smell_name"]
                    if si_smell_type in top_k_pairs:
                        if "introduced_by_refactorings" in si:
                            del si["introduced_by_refactorings"]
                        for ref in si["removed_by_refactorings"]:
                            ref: dict
                            for top_k_r in top_k_pairs[si_smell_type]:
                                if top_k_r==ref["type_name"]:
                                    removed_by_refactorings = [
                                        r for r in si["removed_by_refactorings"] if r["type_name"] == top_k_r
                                    ]
                                    
                                    if f"{si_smell_type}_{top_k_r}" not in all_samples:
                                        all_samples[f"{si_smell_type}_{top_k_r}"] = []
                                    all_samples[f"{si_smell_type}_{top_k_r}"].append({
                                        "repo_full_name": repo_full_name,
                                        "branch": metadata.get("branch", ""),
                                        "smell_versions": si["smell_versions"],
                                        "removed_by_refactorings": removed_by_refactorings,
                                    })
        
        return all_samples
        
    def pick_random_samples(self, smell_type, refactoring_type, samples):
        SEED = 42
        SELECT_SAMPLES = 6
    
        print(f"Total samples collected for {smell_type} and {refactoring_type}: {len(samples)}")
        
        random.seed(SEED)
        selected_samples = []
        
        # Randomly select samples
        if len(samples) <= SELECT_SAMPLES:
            selected_samples = samples
        else:
            selected_samples = random.sample(samples, SELECT_SAMPLES)
        
        print(f"Randomly selected {len(selected_samples)} samples.")
        return selected_samples
                    
    def _get_smell_instance(self, smell_instance_pairs, idx):
        """
        Get a smell instance from the smell instance pairs.
        """
        return smell_instance_pairs[idx]
    
    def save_samples_to_json(self, samples, smell_type, refactoring_type):
        output_dir = config.MANUAL_ANALYSIS_PATH
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_file_path = os.path.join(output_dir, f'{smell_type}_{refactoring_type}.json')
        FileUtils.save_json_file(output_file_path, samples)
        
class UnmappedSampleGenerator:
    def __init__(self):
        self.lib_dir = config.SMELL_REF_MAP_PATH
        self.smell_types = []

    def load_corpus(self):
        df = pd.DataFrame(columns=DF_COLS)
        corpus_bin = os.path.join(self.lib_dir, "corpus.csv")
        if os.path.exists(corpus_bin):
            df = pd.read_csv(corpus_bin, low_memory=False)
            print(f"Loaded corpus with {len(df)} records.")
            print(f"Shape: {df.shape}")
            print(df.head())
            return df
        else:
            raise FileNotFoundError(f"Corpus file not found: {corpus_bin}")
        
    def get_smell_types(self):
        corpus_df = self.load_corpus()
        # Get unique smell types, excluding NaN values
        self.smell_types = corpus_df['smell_type'].dropna().unique().tolist()

    def generate_analysis_samples(self):
        all_samples = self.get_all_samples()
        for smell_type in self.smell_types:
            samples_subset = all_samples.get(f"{smell_type}", [])
            picked_samples = self.pick_random_samples(smell_type, samples_subset)
            
            updated_samples = []
            for s in picked_samples:
                s: dict
                updated_sample = {
                    "human_analysis": {
                        "reason?": ""
                    },
                    **s
                }
                updated_samples.append(updated_sample)
            
            self.save_samples_to_json(updated_samples, smell_type)

    def get_all_samples(self):
        all_samples = {}
        paths = list(FileUtils.traverse_directory(self.lib_dir))
        for file_path in random.sample(paths, len(paths)):
            file_path: str
            if file_path.endswith('.json') and not file_path.endswith('.stats.json') and not file_path.endswith('.chain.json'):
                repo_full_name = os.path.basename(file_path).replace('.json', '')
                map_data = FileUtils.load_json_file(file_path)
                metadata = map_data.get("metadata", {})
                map_chain_data = FileUtils.load_json_file(file_path.replace('.json', '.chain.json'))
                smell_instances = map_data.get("smell_instances", [])
                
                for c in map_chain_data:
                    c: dict
                    
                    latest_chain_item = c.get("chain")[-1]
                    si = self._get_smell_instance(smell_instances, latest_chain_item)
                    
                    si_smell_type = si["smell_versions"][-1]["smell_name"]
                    
                    if si_smell_type in self.smell_types:
                        if f"{si_smell_type}" not in all_samples:
                            all_samples[f"{si_smell_type}"] = []
                        elif len(all_samples[f"{si_smell_type}"]) > 100:
                            continue
                
                        if len(si["removed_by_refactorings"]) == 0 and len(si["introduced_by_refactorings"]) == 0:
                            all_samples[f"{si_smell_type}"].append({
                                "repo_full_name": repo_full_name,
                                "branch": metadata.get("branch", ""),
                                "smell_versions": si["smell_versions"],
                                "commit_versions": si["commit_versions"],
                                "introduced_by_refactorings": si["introduced_by_refactorings"],
                                "removed_by_refactorings": si["removed_by_refactorings"],
                            })
        
        return all_samples

    def pick_random_samples(self, smell_type, samples):
        SEED = 42
        SELECT_SAMPLES = 10
    
        print(f"Total samples collected for {smell_type}: {len(samples)}")
        
        random.seed(SEED)
        selected_samples = []
        
        # Randomly select samples
        if len(samples) <= SELECT_SAMPLES:
            selected_samples = samples
        else:
            selected_samples = random.sample(samples, SELECT_SAMPLES)
        
        print(f"Randomly selected {len(selected_samples)} samples.")
        return selected_samples

    def _get_smell_instance(self, smell_instance_pairs, idx):
        """
        Get a smell instance from the smell instance pairs.
        """
        return smell_instance_pairs[idx]

    def save_samples_to_json(self, samples, smell_type):
        output_dir = config.MANUAL_ANALYSIS_FOR_UNMAPPED_PATH
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_file_path = os.path.join(output_dir, f'{smell_type}.json')
        FileUtils.save_json_file(output_file_path, samples)

def group_unmapped_manual_analysis_results():
    target_dir = config.MANUAL_ANALYSIS_FOR_UNMAPPED_PATH
    reason_to_files = {}

    for f in FileUtils.traverse_directory(target_dir):
        f_data = FileUtils.load_json_file(f)
        for d in f_data:
            reason = d["human_analysis"]["reason?"]
            if reason and reason.strip():  # Skip empty or whitespace-only reasons
                file_basename = os.path.basename(f).split('.')[0]
                if reason not in reason_to_files:
                    reason_to_files[reason] = {}
                if file_basename not in reason_to_files[reason]:
                    reason_to_files[reason][file_basename] = 0
                reason_to_files[reason][file_basename] += 1

    # Create a DataFrame where reasons are columns and smell names are rows
    all_smell_names = sorted({smell for smells in reason_to_files.values() for smell in smells})
    all_reasons = sorted(reason_to_files.keys())

    table_data = []
    for smell_name in all_smell_names:
        row = []
        for reason in all_reasons:
            row.append(reason_to_files.get(reason, {}).get(smell_name, 0))
        table_data.append(row)

    reason_smell_table = pd.DataFrame(table_data, index=all_smell_names, columns=all_reasons)
    print("\nReason-Smell Table:")
    print(reason_smell_table)

    # Save the table to a CSV file
    output_csv_path = os.path.join(config.OUTPUT_PATH, "reason_unmapped_smell_table.csv")
    reason_smell_table.to_csv(output_csv_path)
    print(f"Reason-Smell Table saved to {output_csv_path}")

def calculate_kappa():
    human_res = []
    llm_res = []
    
    target_dir = config.MANUAL_ANALYSIS_PATH
    for f in FileUtils.traverse_directory(target_dir):        
        f_data = FileUtils.load_json_file(f)
        
        for d in f_data:
            try:
                human_res.append(d["human_analysis"]["correct_mapping?"])
                llm_res.append(d["llm_analysis"]["correct_mapping?"])
            except Exception as e:
                print(f"An error occurred: {e}")
        
    # Calculate Cohen's Kappa score
    kappa_score = cohen_kappa_score(human_res, llm_res)
    print(f"Cohen's Kappa Score: {kappa_score}")