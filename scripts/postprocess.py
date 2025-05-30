import os
import time
import config
from utils import FileUtils, hashgen

class CorpusAnalyzer:
    def __init__(self):
        self.lib_dir = config.SMELL_REF_MAP_PATH
        self.maps_finsihed = 1
        self.TOTAL_MAPS = 86
        self.total_smells = 0
        self.smells_merged = 0
        self.alive_smells = 0
        self.removed_smells = 0
        
    def process_corpus(self):
        # limit = 0
        for map_file_path in FileUtils.traverse_directory(self.lib_dir):
            map_file_path: str
            # if limit == 1:
            #     break
            if map_file_path.endswith('.json') and not map_file_path.endswith('.stats.json') and not map_file_path.endswith('.chain.json'):
                print(f"Processing {map_file_path}")
                self.process_repo(map_file_path, print_log=True)  
                print(f"Processed {self.maps_finsihed}/{self.TOTAL_MAPS} | {map_file_path}\n")
                self.maps_finsihed += 1
                # limit += 1
                
                
        print(f"Total smell instances: {self.total_smells}")
        print(f"Total smells merged: {self.smells_merged}")
        print(f"Total alive smells: {self.alive_smells}")
        print(f"Total removed smells: {self.removed_smells}")
    
    def process_repo(self, repo_map_path, print_log=False):
        repo_full_name = os.path.basename(repo_map_path).replace('.json', '')
        map_data = FileUtils.load_json_file(repo_map_path)
        smell_instances: list[dict] = map_data.get("smell_instances", [])
        smell_instances = self.transform_refs_to_hash(smell_instances)
        
        chain_data = {}
        smell_space = list(range(0, len(smell_instances)))
        introduced_map = self.generate_introduced_map(smell_instances)
        
        recursion_start_time = time.time()
        recursion_limit = 10
        def find_chain(p_smell_kind: str, p_smell_type: str, p_removed_hash, p_removed_refs: list[tuple]):
            """
            Find the chain of smell instances that are related to each other.
            """
            if time.time() - recursion_start_time > recursion_limit:
                return []
            chain = []
            
            # check if the removed hash is in the introduced map
            for idx in introduced_map.get(p_removed_hash, []):
                smell_kind, smell_type = self._get_smell_info(smell_instances[idx])
                removed_hash = self._get_removed_commit_hash(smell_instances[idx])
                introduced_by_refs = smell_instances[idx]["introduced_by_refactorings"]
                removed_by_refs = smell_instances[idx]["removed_by_refactorings"]
                if smell_kind == p_smell_kind and smell_type == p_smell_type:
                    for ref in p_removed_refs:
                        if ref in introduced_by_refs:
                            chain.append(idx)
                            if idx in smell_space:
                                smell_space.remove(idx)
                            chain.extend(find_chain(smell_kind, smell_type, removed_hash, removed_by_refs))
                        break
            
            return chain
        
        total_smell_instances = len(smell_instances)
        for idx, smell_inst in enumerate(smell_instances):
            # print(f"\rSmells progress: {idx}/{total_smell_instances}", end="", flush=True)
            if not smell_inst.get("is_alive"):
                if idx not in chain_data and idx in smell_space:
                    chain_data[idx] = {
                        "chain": [],
                        "is_alive": False
                    }
                    smell_space.remove(idx)
    
                    # check for chain
                    smell_kind, smell_type = self._get_smell_info(smell_inst)
                    
                    removed_hash = self._get_removed_commit_hash(smell_inst)
                    removed_by_refs = smell_inst["removed_by_refactorings"]
                    
                    if len(removed_by_refs) > 0:
                        chain = find_chain(smell_kind, smell_type, removed_hash, removed_by_refs)
                        chain_data[idx]["chain"] = chain
                        
                        if chain != []:
                            chain_data[idx]["is_alive"] = smell_instances[chain[-1]]["is_alive"]
                        else:
                            chain_data[idx]["is_alive"] = smell_instances[idx]["is_alive"]
                            
        # handle solo alive instances
        for idx in smell_space[:]:
            smell_status = smell_instances[idx]["is_alive"]
            chain_data[idx] = {
                "chain": [],
                "is_alive": smell_status
            }
            smell_space.remove(idx)
        
        # sort chain_data
        chain_data = dict(sorted(chain_data.items(), key=lambda item: item[0]))
        
        final_chain_data = []
        for idx, data in chain_data.items():
            chain = [idx] + data["chain"]
            final_chain_data.append({
                "chain": chain,
                "is_alive": data["is_alive"]
            })
            
        total_alive_final = sum(1 for data in final_chain_data if data["is_alive"])
        total_not_alive_final = len(final_chain_data) - total_alive_final
        
        if print_log:
            # no smell chain should be left
            print(f"\n(should be always 0) Smell instances left behind ({len(smell_space)}): {smell_space}")
            print(f"Total smell instances after merge, from {len(smell_instances)} -> {len(chain_data)} (merged - {len(smell_instances) - len(chain_data)})")
            # print total alive and removed smells from final_chain_data
            print(f"Total alive smells in final_chain_data: {total_alive_final}")
            print(f"Total removed smells in final_chain_data: {total_not_alive_final}")
        
        self.total_smells += len(smell_instances)
        self.smells_merged += len(smell_instances) - len(chain_data)
        self.alive_smells += total_alive_final
        self.removed_smells += total_not_alive_final    
        
        self.save_repo_smell_chain(repo_full_name, final_chain_data)
        
    def _get_smell_info(self, smell_instance):
        default_smell_v = smell_instance["smell_versions"][-1]
        smell_kind = default_smell_v["smell_kind"]
        smell_type = default_smell_v["smell_name"]
        # smell_cause = default_smell_v["cause"]
        return smell_kind, smell_type
    
    def _get_introduced_commit_hash(self, smell_instance):
        commit_versions = smell_instance["commit_versions"]
        
        return commit_versions[0]["commit_hash"]
    
    def transform_refs_to_hash(self, smell_instances):
        for smell_inst in smell_instances:
            introduced_by_refs = smell_inst["introduced_by_refactorings"]
            hashed_introduced_by_refs = []
            for ref in introduced_by_refs:
                ref_hash = hashgen(ref)
                hashed_introduced_by_refs.append(ref_hash)
            smell_inst["introduced_by_refactorings"] = hashed_introduced_by_refs  
            
            removed_by_refs = smell_inst["removed_by_refactorings"]
            hashed_removed_by_refs = []
            for ref in removed_by_refs:
                ref_hash = hashgen(ref)
                hashed_removed_by_refs.append(ref_hash)
            
            smell_inst["removed_by_refactorings"] = hashed_removed_by_refs
        return smell_instances
    
    def _get_removed_commit_hash(self, smell_instance):
        commit_versions = smell_instance["commit_versions"]
        is_alive = smell_instance["is_alive"]
        if is_alive:
            return None
        else:
            return commit_versions[-1]["commit_hash"]
    
    def generate_introduced_map(self, smell_instance: list):
        map = {}
        for idx, smell_inst in enumerate(smell_instance):
            introduced_hash = self._get_introduced_commit_hash(smell_inst)
            if introduced_hash not in map:
                map[introduced_hash] = []
            map[introduced_hash].append(idx)
        return map
    
    def save_repo_smell_chain(self, repo_map_name, chain_data):
        """
        Save the calculated statistics for the corpus.
        """
        top_k_corpus_stats_path = os.path.join(self.lib_dir, f'{repo_map_name}.chain.json')
        FileUtils.save_json_file(top_k_corpus_stats_path, chain_data)

if __name__ == "__main__":
    analyzer = CorpusAnalyzer()
    analyzer.process_corpus()