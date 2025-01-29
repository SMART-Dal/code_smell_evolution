import os
import config
from utils import FileUtils
from models import DESIGN_SMELL, IMP_SMELL

class CorpusAnalyzer:
    def __init__(self):
        self.lib_dir = config.SMELL_REF_MAP_PATH
        self.plots_dir = config.PLOTS_PATH
        if not os.path.exists(self.plots_dir):
            os.makedirs(self.plots_dir)
            
    def process(self):
        for file_path in FileUtils.traverse_directory(self.lib_dir):
            file_path: str
            if file_path.endswith('.json') and not file_path.endswith('.stats.json'):
                repo_full_name = os.path.basename(file_path).replace('.json', '')
                repo_data = FileUtils.load_json_file(file_path)
                
                self.calculate_repo_stats(file_path, repo_data)
            
    def calculate_repo_stats(self, repo_data_path, repo_data):
        """
        Calculate smell instance statistics.
        """
        smell_instance_pairs = repo_data.get("smell_instances", [])
        lifespan_stats = {
            "total_smell_instances": len(smell_instance_pairs),
            "resolved_smells": {
                "total": 0,
                DESIGN_SMELL: {},
                IMP_SMELL: {}
            },
            "unresolved_smells": {
                "total": 0,
                DESIGN_SMELL: {},
                IMP_SMELL: {}
            },   
            "never_introduced_by_refactorings": 0,
            "never_resolved_by_refactorings": 0
        }
        
        for smell_instance in smell_instance_pairs:
            is_smell_instance_alive = smell_instance.get("is_alive", False)
            smell_instance_smell_kind = smell_instance["smell_versions"][0]["smell_kind"]
            smell_instance_smell_type = smell_instance["smell_versions"][0]["smell_name"]
            
            introduced_by_refactorings = smell_instance.get("introduced_by_refactorings", [])
            if len(introduced_by_refactorings) == 0:
                lifespan_stats["never_introduced_by_refactorings"] += 1
            refs_count_introduced = self.get_refactorings_stats(introduced_by_refactorings)
            
            if is_smell_instance_alive:
                lifespan_stats["unresolved_smells"]["total"] += 1
                self._update_refactoring_counts(lifespan_stats["unresolved_smells"], smell_instance_smell_kind, smell_instance_smell_type, refs_count_introduced)
            else:
                lifespan_stats["resolved_smells"]["total"] += 1
                
                removed_by_refactorings = smell_instance.get("removed_by_refactorings", [])
                if len(removed_by_refactorings) == 0:
                    lifespan_stats["never_resolved_by_refactorings"] += 1
                refs_count_removed = self.get_refactorings_stats(removed_by_refactorings)
                self._update_refactoring_counts(lifespan_stats["resolved_smells"], smell_instance_smell_kind, smell_instance_smell_type, refs_count_removed)

        self._add_stats('lifespan_stats', lifespan_stats, repo_data_path)
        
    def get_refactorings_stats(self, refs_list):
        """
        Calculate refactoring statistics.
        """
        refs_count = {}
        for ref in refs_list:
            type_name = ref.get("type_name")
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
            
        # Insert the new data at the top of the existing data
        updated_stats_data = {new_data_key: new_data_dict}
        if new_data_key in stats_data:
            del stats_data[new_data_key]
        updated_stats_data.update(stats_data)
        
        FileUtils.save_json_file(stats_file_path, updated_stats_data)