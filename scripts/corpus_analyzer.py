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
    "total_span", "introduced_commit_hash", "introduced_commit_date", "removed_commit_hash", "removed_commit_date"
]

BATCH_SIZE = 10
MAX_THREADS = 2
class CorpusAnalyzer:
    def __init__(self):
        self.lib_dir = config.SMELL_REF_MAP_PATH
        self.plots_dir = config.PLOTS_PATH
        os.makedirs(self.plots_dir, exist_ok=True)
        self.corpus_bin = os.path.join(self.lib_dir, "corpus.csv")
        # self.corpus = self.load_corpus()
            
    def load_corpus(self):
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
            print(f"\rProcessed {count}/{total_maps} maps.", end="", flush=True)
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
            del si["smell_versions"]
            
            # commit info
            si["introduced_commit_hash"] = si["commit_versions"][0]["commit_hash"]
            si["introduced_commit_date"] = si["commit_versions"][0]["datetime"]
            si["removed_commit_hash"] = si["commit_versions"][-1]["commit_hash"]
            si["removed_commit_date"] = si["commit_versions"][-1]["datetime"]
            del si["commit_versions"]
            
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
            is_alive = c.get("is_alive")
            
            # commit info
            # total commits span, introudced hash and date, removed hash and date
            t, i_h, i_d, r_h, r_d = self._get_commit_info(smell_instances, c)
           
            data.append({
                "repo_name": repo_name,
                "smell_kind": smell_kind,
                "smell_type": smell_type,
                "is_alive": is_alive,
                "movements": len(si["smell_versions"]), # number of movements soley based on smell info
                "chain_length": len(c.get("chain")),
                "total_span": t,
                "introduced_commit_hash": i_h,
                "introduced_commit_date": i_d,
                "removed_commit_hash": r_h,
                "removed_commit_date": r_d
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
        
        for i, c in enumerate(chain.get("chain", [])):
            si = self._get_smell_instance(smell_instance_pairs, c)
            if i == 0:
                introduced_commit_hash = si["commit_versions"][0]["commit_hash"]
                introduced_commit_date = si["commit_versions"][0]["datetime"]
            if i == len(chain.get("chain")) - 1:
                removed_commit_hash = si["commit_versions"][-1]["commit_hash"]
                removed_commit_date = si["commit_versions"][-1]["datetime"]
                
        return introduced_commit_hash, introduced_commit_date, removed_commit_hash, removed_commit_date