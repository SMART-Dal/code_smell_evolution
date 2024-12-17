import os
from datetime import datetime
from runners import Designite, RefMiner, PyDriller
import config
from utils import GitManager
from utils import log_execution, load_csv_file, traverse_directory, load_json_file, save_json_file, get_smell_dict

class RepoDataAnalyzer:
    def __init__(self, repo_path: str, branch: str):
        self.repo_name = os.path.basename(repo_path)
        self.repo_path = repo_path
        self.repo_designite_output_path = os.path.join(Designite.output_dir, self.repo_name)
        self.repo_refminer_output_path = os.path.join(RefMiner.output_dir, f"{self.repo_name}.json")
        self.branch = branch
        self.active_commits: list[tuple[str, datetime]] = []
        self.all_commits: list[tuple[str, datetime]] = GitManager.get_all_commits(repo_path, branch)
        
        self.arch_smells = {}
        self.design_smells = {}
        self.impl_smells = {}
        self.testability_smells = {}
        self.test_smells = {}
        
        self.method_metrics = {}
        
        self.refactorings = {}
        
        self.smells_lifespan_history = []
        self.load_smells()
        self.load_refactorings()
        
    @log_execution
    def load_smells(self):
        for commit_path in traverse_directory(self.repo_designite_output_path):
            commit_hash = os.path.basename(commit_path)
            commit_datetime = next((dt for ch, dt in self.all_commits if ch == commit_hash), None)
            if commit_datetime:
                self.active_commits.append((commit_hash, commit_datetime))
            
            csv_files = [
                ("ArchitectureSmells.csv", self.arch_smells),
                ("DesignSmells.csv", self.design_smells),
                ("ImplementationSmells.csv", self.impl_smells),
                ("TestabilitySmells.csv", self.testability_smells),
                ("TestSmells.csv", self.test_smells),
                ("MethodMetrics.csv", self.method_metrics)
            ]
            
            for csv_file, smell_dict in csv_files:
                csv_path = os.path.join(commit_path, csv_file)
                if os.path.exists(csv_path):
                    smell_dict[commit_hash] = load_csv_file(csv_path, skipCols=config.SMELL_SKIP_COLS)
    
    @log_execution
    def load_refactorings(self):
        for commit in load_json_file(self.repo_refminer_output_path).get("commits"):
            if any(commit.get("sha1") == active_commit[0] for active_commit in self.active_commits):
                self.refactorings[commit.get("sha1")] = commit.get("refactorings")
    
    @log_execution     
    def calculate_smells_lifespan(self):
        sorted_active_commits = sorted(self.active_commits, key=lambda x: x[1])
        smells_lifespan = {}
        
        previous_commit = None
        for commit_hash, commit_datetime in sorted_active_commits:
            if previous_commit:
                for smell_dict in [self.arch_smells, self.design_smells, self.impl_smells, self.testability_smells, self.test_smells]:
                    
                    added_smells = set()
                    removed_smells = set()
                    previous_smells = smell_dict.get(previous_commit)
                    current_smells = smell_dict.get(commit_hash)
                    
                    if previous_smells and current_smells:
                        added_smells = set(map(str, current_smells)) - set(map(str, previous_smells))
                        removed_smells = set(map(str, previous_smells)) - set(map(str, current_smells))
                    elif current_smells and not previous_smells:
                        added_smells = set(map(str, current_smells))
                        
                    for smell in added_smells:
                        smells_lifespan[smell] = {"introduced": commit_datetime, "removed": None, "introduced_commit": commit_hash, "removed_commit": None}
                    for smell in removed_smells:
                        if smell in smells_lifespan:
                            smells_lifespan[smell]["removed"] = commit_datetime
                            smells_lifespan[smell]["removed_commit"] = commit_hash
                            self.smells_lifespan_history.append((smell, smells_lifespan[smell]))
                            del smells_lifespan[smell]
            else:
                for smell_dict in [self.arch_smells, self.design_smells, self.impl_smells, self.testability_smells, self.test_smells]:
                    current_smells = smell_dict.get(commit_hash)
                    
                    if current_smells:
                        for smell in map(str, current_smells):
                            smells_lifespan[smell] = {"introduced": commit_datetime, "removed": None, "introduced_commit": commit_hash, "removed_commit": None}
            
            previous_commit = commit_hash
            
        for smell, data in smells_lifespan.items():
            self.smells_lifespan_history.append((smell, data))
        
        # NOTE: optional sorting by introduced date
        self.smells_lifespan_history.sort(key=lambda x: x[1]["introduced"])
        
        self.calculate_lifespan_gap()
    
    @log_execution
    def calculate_lifespan_gap(self):
        for smell, data in self.smells_lifespan_history:
            if data["introduced"] and data["removed"]:
                data["days_span"] = (data["removed"] - data["introduced"]).days
                introduced_index = next(i for i, (ch, _) in enumerate(self.all_commits) if ch == data["introduced_commit"])
                removed_index = next(i for i, (ch, _) in enumerate(self.all_commits) if ch == data["removed_commit"])
                data["commit_span"] =  introduced_index - removed_index
    
    @log_execution
    def map_refactorings_to_smells(self):
        for smell, data in self.smells_lifespan_history:
            data["unmapped_refactorings"] = []
            for commit_hash, refactorings in self.refactorings.items():
                if commit_hash == data["removed_commit"]:
                    data["unmapped_refactorings"] = refactorings
                    break
                
        for smell, data in self.smells_lifespan_history:
            smell_range = data.get("range", None)
            unmapped_refactorings = data.get("unmapped_refactorings", [])
            mapped_refactorings = []
            if smell_range is None:
                data["mapped_refactorings"] = unmapped_refactorings
                continue
            
            for refactoring in unmapped_refactorings:
                for location in refactoring["rightSideLocations"]:
                    if smell_range[0] <= location["startLine"] <= smell_range[1] or smell_range[0] <= location["endLine"] <= smell_range[1]:
                        mapped_refactorings.append(refactoring)
                        break
            
            data["mapped_refactorings"] = mapped_refactorings
            
    @log_execution
    def calc_smell_range(self):
        
        def java_file_path(info):
            package_name = info.get('Package Name', '').replace('.', '/')
            type_name = info.get('Type Name', '') + ".java"
             # Combine base directory, package path, and file name
            if package_name and type_name:
                return f"{package_name}/{type_name}"
                # return f"src/main/java/{package_name}/{type_name}"
            else:
                raise ValueError("Invalid input: 'Package Name' or 'Type Name' is missing.")
        
        commits_to_cover = [commit[0] for commit in self.active_commits]
        methods_data_map: dict[str, dict] = PyDriller.get_methods_map(self.repo_path, self.branch, commits_to_cover)
        
        for smell, data in self.smells_lifespan_history:
            smell_dict = get_smell_dict(smell)
            smell_path = java_file_path(smell_dict)
            smell_method_name = None
            if smell_dict.get("Method Name"):
                smell_method_name = smell_dict.get("Method Name")
            
            introduced_commit_hash = data.get("introduced_commit")
            for file_path, methods_data in methods_data_map.get(introduced_commit_hash, {}).items():
                file_path: str
                methods_data: dict
                if file_path and smell_path and file_path.endswith(smell_path):
                    for method_name, method_range in methods_data.items():
                        method_name: str
                        method_range: tuple
                        method_name_split = method_name.split('::')
                        if smell_method_name and smell_method_name in method_name_split:
                            data["range"] = method_range
                            break
            
    
    @log_execution
    def save_lifespan_to_json(self):
        for  _, data in self.smells_lifespan_history:
            del data["unmapped_refactorings"]
        
        serializable_lifespan = {
            smell: {
                key: (value.isoformat() if isinstance(value, datetime) else value)
                for key, value in data.items()
            }
            for smell, data in self.smells_lifespan_history
        }
        save_json_file(os.path.join(config.SMELLS_LIB_PATH, f"{os.path.basename(self.repo_path)}.json"), data=serializable_lifespan)