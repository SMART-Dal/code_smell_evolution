import os
from datetime import datetime
from runners import Designite
import config
from utils import RepoManager, load_csv_file, traverse_directory, save_json_file

class RepoDataAnalyzer:
    def __init__(self, repo_name:str, repo_path: str, branch: str):
        self.repo_path = repo_path
        self.repo_output_path = os.path.join(Designite.output_dir, repo_name)
        self.branch = branch
        self.active_commits: list[tuple[str, datetime]] = []
        self.all_commits: list[tuple[str, datetime]] = RepoManager.get_all_commits(repo_path, branch)
        
        self.arch_smells = {}
        self.design_smells = {}
        self.impl_smells = {}
        self.testability_smells = {}
        self.test_smells = {}
        self.smells_lifespan = {}
        self.load_smells()

    def load_smells(self):
        for commit_path in traverse_directory(self.repo_output_path):
            commit_hash = os.path.basename(commit_path)
            commit_datetime = next((dt for ch, dt in self.all_commits if ch == commit_hash), None)
            if commit_datetime:
                self.active_commits.append((commit_hash, commit_datetime))
            
            csv_files = [
                ("ArchitectureSmells.csv", self.arch_smells),
                ("DesignSmells.csv", self.design_smells),
                ("ImplementationSmells.csv", self.impl_smells),
                ("TestabilitySmells.csv", self.testability_smells),
                ("TestSmells.csv", self.test_smells)
            ]
            
            for csv_file, smell_dict in csv_files:
                csv_path = os.path.join(commit_path, csv_file)
                if os.path.exists(csv_path):
                    smell_dict[commit_hash] = load_csv_file(csv_path)
                    
    def calculate_smells_lifespan(self):
        sorted_active_commits = sorted(self.active_commits, key=lambda x: x[1])
        previous_commit = None
        for commit_hash, commit_datetime in sorted_active_commits:
            if previous_commit:
                for smell_dict in [self.arch_smells, self.design_smells, self.impl_smells, self.testability_smells, self.test_smells ]:
                    
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
                        self.smells_lifespan[smell] = {"introduced": commit_datetime, "removed": None}
                    for smell in removed_smells:
                        if smell in self.smells_lifespan:
                            self.smells_lifespan[smell]["removed"] = commit_datetime
            else:
                for smell_dict in [self.arch_smells, self.design_smells, self.impl_smells, self.testability_smells, self.test_smells]:
                    current_smells = smell_dict.get(commit_hash)
                    
                    if current_smells:
                        for smell in map(str, current_smells):
                            self.smells_lifespan[smell] = {"introduced": commit_datetime, "removed": None}
            
            previous_commit = commit_hash
            
    def calculate_lifespan_gap(self):
        for smell, data in self.smells_lifespan.items():
            if data["introduced"] and data["removed"]:
                data["span"] = (data["removed"] - data["introduced"]).days
            
    def save_lifespan_to_json(self):
        serializable_lifespan = {
            smell: {
                "introduced": data["introduced"].isoformat() if data["introduced"] else None,
                "removed": data["removed"].isoformat() if data["removed"] else None,
                "span": data["span"] if "span" in data else None
            }
            for smell, data in self.smells_lifespan.items()
        }
        save_json_file(os.path.join(config.OUTPUT_PATH, "SmellsLifespan.json"), serializable_lifespan)