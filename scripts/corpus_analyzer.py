import os
import config
import itertools
import concurrent.futures
import pandas as pd
import numpy as np
from utils import FileUtils

DF_COLS = [
    "repo_name", "smell_kind", "smell_type", "is_alive",
    "movements", "chain_length",
    "total_commits_span", "total_days_span",
    "introduced_commit_hash", "introduced_commit_date",
    "removed_commit_hash", "removed_commit_date",
    "introduction_refactorings", "removal_refactorings",
]

BATCH_SIZE = 10
MAX_THREADS = 4
class CorpusAnalyzer:
    def __init__(self):
        self.lib_dir = config.SMELL_REF_MAP_PATH
        self.plots_dir = config.PLOTS_PATH
        os.makedirs(self.plots_dir, exist_ok=True)
        self.corpus_bin = os.path.join(self.lib_dir, "corpus.csv")
        self.corpus_df = pd.DataFrame(columns=DF_COLS)
        
    def load_corpus(self):
        """
        Load the corpus if it exists, otherwise generate it.
        """
        if os.path.exists(self.corpus_bin):
            self.corpus_df = self.read_corpus()
            print(f"Loaded corpus with {len(self.corpus_df)} records.")
            print(f"Shape: {self.corpus_df.shape}")
        else:
            print(f"Corpus file not found: {self.corpus_bin}. Generating corpus...")
            self.generate_corpus()
            self.corpus_df = self.read_corpus()
        
    def read_corpus(self):
        """
        Read the corpus from the CSV file.
        """
        if not os.path.exists(self.corpus_bin):
            raise FileNotFoundError(f"Corpus file not found: {self.corpus_bin}")
        
        df = pd.read_csv(self.corpus_bin)
        return df
            
    def generate_corpus(self):
        maps = [
            file_path for file_path in FileUtils.traverse_directory(self.lib_dir)
            if file_path.endswith('.json') and not file_path.endswith('.stats.json') and not file_path.endswith('.chain.json')
        ]
        total_maps = len(maps)
        print(f"Found {total_maps} maps to process.")
        
        processed = itertools.count(1)  # thread-safe counter
        
        def process_map(file_path):
            repo_full_name = os.path.basename(file_path).replace('.json', '')
            smell_instances, map_chain_data = self.get_repo_data(file_path)
            result = self.convert_to_rows(repo_full_name, smell_instances, map_chain_data)
            count = next(processed)
            # print(f"\rProcessed {count}/{total_maps} maps.", end="", flush=True)
            return result
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(process_map, file_path) for file_path in maps]

            # with open(self.corpus_bin, "w") as f:
            #     f.write(",".join(DF_COLS) + "\n")  # Write headers

            batch = []
            for future in concurrent.futures.as_completed(futures):
                batch.extend(future.result())

                if len(batch) >= BATCH_SIZE:
                    self._write_to_csv(batch)
                    batch.clear()

        if batch:
            self._write_to_csv(batch)

        print(f"\nCorpus saved at {self.corpus_bin}")
        
    def get_repo_data(self, map_path):
        map_data = FileUtils.load_json_file(map_path)
        map_chain_data = FileUtils.load_json_file(map_path.replace('.json', '.chain.json'))
        smell_instances = map_data.get("smell_instances", [])
        
        # normalize smell instances for data analysis
        for si in smell_instances:
            
            si["smell_kind"] = si["smell_versions"][-1]["smell_kind"]
            si["smell_type"] = si["smell_versions"][-1]["smell_name"]
            # del si["smell_versions"]
            
            # commit info
            si["introduced_commit_hash"] = si["commit_versions"][0]["commit_hash"]
            si["introduced_commit_date"] = si["commit_versions"][0]["datetime"]
            si["removed_commit_hash"] = si["commit_versions"][-1]["commit_hash"]
            si["removed_commit_date"] = si["commit_versions"][-1]["datetime"]
            # del si["commit_versions"]
            
            # refactorings pairs
            if si.get("introduced_by_refactorings"):
                si["introduced_by_refactorings"] = [ref["type_name"] for ref in si["introduced_by_refactorings"]]
            if si.get("removed_by_refactorings"):
                si["removed_by_refactorings"] = [ref["type_name"] for ref in si["removed_by_refactorings"]]
        
        return smell_instances, map_chain_data
        
    def _write_to_csv(self, batch):
        df = pd.DataFrame(batch, columns=DF_COLS)
        df.to_csv(self.corpus_bin, mode="a", index=False, header=not os.path.exists(self.corpus_bin))
                
    def convert_to_rows(self, repo_name: str, smell_instances: dict, map_chain_data: list):
        data = []
        for c in map_chain_data:
            latest_chain_item = c.get("chain")[-1]
            si = self._get_smell_instance(smell_instances, latest_chain_item)

            # smells info
            smell_kind = si["smell_versions"][-1]["smell_kind"]
            smell_type = si["smell_versions"][-1]["smell_name"]
            package_name = si["smell_versions"][-1]["package_name"]
            type_name = si["smell_versions"][-1]["type_name"]
            method_name = si["smell_versions"][-1]["method_name"]
            is_alive = c.get("is_alive")
            
            # commit info
            # total commits span, introudced hash and date, removed hash and date
            i_h, i_d, r_h, r_d, span_c, span_d = self._get_commit_info(smell_instances, c)
            i_refs, r_refs = self._get_refactoring_info(smell_instances, c)
           
            data.append({
                "repo_name": repo_name,
                "package": package_name,
                "type": type_name,
                "method": method_name,
                "smell_kind": smell_kind,
                "smell_type": smell_type,
                "is_alive": is_alive,
                "movements": len(si["smell_versions"]), # number of movements soley based on smell info
                "chain_length": len(c.get("chain")),
                "total_commits_span": span_c,
                "total_days_span": span_d,
                "introduced_commit_hash": i_h,
                "introduced_commit_date": i_d,
                "removed_commit_hash": None if is_alive else r_h,
                "removed_commit_date": None if is_alive else r_d,
                "introduction_refactorings": i_refs,
                "removal_refactorings": None if is_alive else r_refs,
            })
        
        return data

    def _get_smell_instance(self, smell_instance_pairs, idx):
        """
        Get a smell instance from the smell instance pairs.
        """
        return smell_instance_pairs[idx]
    
    def _get_commit_info(self, smell_instance_pairs, chain):
        """
        Get the total commit span of a smell instance.
        """
        introduced_commit_hash = None
        introduced_commit_date = None
        removed_commit_hash = None
        removed_commit_date = None
        span_c = 0
        span_d = 0
        
        for i, c in enumerate(chain.get("chain", [])):
            si = self._get_smell_instance(smell_instance_pairs, c)
            if i == 0:
                introduced_commit_hash = si["commit_versions"][0]["commit_hash"]
                introduced_commit_date = si["commit_versions"][0]["datetime"]
            if i == len(chain.get("chain")) - 1:
                removed_commit_hash = si["commit_versions"][-1]["commit_hash"]
                removed_commit_date = si["commit_versions"][-1]["datetime"]
            span_c += int(si["commit_span"]) if si["commit_span"] is not None else 0
            span_d += int(si["days_span"]) if si["days_span"] is not None else 0
                
        return introduced_commit_hash, introduced_commit_date, removed_commit_hash, removed_commit_date, span_c, span_d
    
    def _get_refactoring_info(self, smell_instance_pairs, chain):
        """
        Get the refactoring info of a smell instance.
        """
        DELIMITER = ";"
                
        first_chain_item = chain.get("chain")[0]
        first_si = self._get_smell_instance(smell_instance_pairs, first_chain_item)
        
        last_chain_item = chain.get("chain")[-1]
        last_si = self._get_smell_instance(smell_instance_pairs, last_chain_item)
        
        return DELIMITER.join(set(first_si.get("introduced_by_refactorings", []))), DELIMITER.join(set(last_si.get("removed_by_refactorings", [])))