import os
from datetime import datetime
from runners import Designite, RefMiner, PyDriller
import config
from utils import GitManager, ColoredStr
from utils import log_execution, load_csv_file, traverse_directory, load_json_file, save_json_file
from models import SmellInstance, ArchitectureSmell, DesignSmell, ImplementationSmell, TestabilitySmell, TestSmell, Refactoring

class RepoDataAnalyzer:
    def __init__(self, username: str, repo_name: str, repo_path: str, branch: str):
        self.repo_path = repo_path
        self.repo_designite_output_path = os.path.join(Designite.output_dir, username, repo_name)
        self.repo_refminer_output_path = os.path.join(RefMiner.output_dir, username, f"{repo_name}.json")
        
        self.branch = branch
        self.active_commits: list[tuple[str, datetime]] = []
        self.all_commits: list[tuple[str, datetime]] = GitManager.get_all_commits(repo_path, branch)
        
        self.architecture_smells: dict[str, list[ArchitectureSmell]] = {}
        self.design_smells: dict[str, list[DesignSmell]] = {}
        self.implementation_smells: dict[str, list[ImplementationSmell]] = {}
        self.testability_smells: dict[str, list[TestabilitySmell]] = {}
        self.test_smells: dict[str, list[TestSmell]] = {}
        
        self.refactorings: dict[str, list[Refactoring]] = {}
        
        self.smells_lib: list[SmellInstance] = []
        self.load_raw_smells()
        self.load_raw_refactorings()
        
        #metadata
        self.present_smell_types = {}
        self.present_refactoring_types = []
        
    @log_execution
    def load_raw_smells(self):
        """
        Load raw smells from Designite output.
        Will load smells for active commits only.
        """
        for commit_path in traverse_directory(self.repo_designite_output_path):
            commit_hash = os.path.basename(commit_path)
            commit_datetime = next((dt for ch, dt in self.all_commits if ch == commit_hash), None)
            if commit_datetime:
                self.active_commits.append((commit_hash, commit_datetime))
            
            csv_files = [
                ("ArchitectureSmells.csv", self.architecture_smells, ArchitectureSmell),
                ("DesignSmells.csv", self.design_smells, DesignSmell),
                ("ImplementationSmells.csv", self.implementation_smells, ImplementationSmell),
                ("TestabilitySmells.csv", self.testability_smells, TestabilitySmell),
                ("TestSmells.csv", self.test_smells, TestSmell),
            ]
            
            for csv_file, smell_dict, smell_model in csv_files:
                csv_path = os.path.join(commit_path, csv_file)
                if os.path.exists(csv_path):
                    smell_instances = []
                    smell_hashes = set()
                    smells_data = load_csv_file(csv_path, skipCols=config.SMELL_SKIP_COLS)
                    for smell_row in smells_data:
                        pakage_name = smell_row.get("Package Name", None)
                        smell_name = smell_row.get(smell_model.kind, None)
                        cause = smell_row.get("Cause of the Smell", None)
                        smell_instance = smell_model(pakage_name, smell_name, cause)
                        
                        if smell_model in [DesignSmell, TestabilitySmell]:
                            smell_instance.type_name = smell_row.get("Type Name", None)
                        elif smell_model in [TestSmell]:
                            smell_instance.type_name = smell_row.get("Type Name", None)
                            smell_instance.method_name = smell_row.get("Method Name", None)
                        elif smell_model in [ImplementationSmell]:
                            smell_instance.type_name = smell_row.get("Type Name", None)
                            smell_instance.method_name = smell_row.get("Method Name", None)
                            smell_instance.start_line = smell_row.get("Method start line no", None)
                        
                        if hash(smell_instance) in smell_hashes: # remove duplicates
                            continue
                        
                        smell_instances.append(smell_instance)
                        smell_hashes.add(hash(smell_instance))
                    
                    smell_dict[commit_hash] = smell_instances
    
    @log_execution
    def load_raw_refactorings(self):
        """
        Load raw refactorings from RefMiner output.
        Will load refactorings for active commits only.
        """
        for commit in load_json_file(self.repo_refminer_output_path).get("commits"):
            if any(commit.get("sha1") == active_commit[0] for active_commit in self.active_commits):
                commit_hash = commit.get("sha1")
                refactorings = commit.get("refactorings")
                url = commit.get("url")
                
                refactoring_instances = []
                for refactoring in refactorings:
                    refactoring_instance = Refactoring(url, refactoring.get("type"), commit_hash)
                    for location in refactoring.get("rightSideLocations"):
                        refactoring_instance.add_change(
                            file_path=location.get("filePath"), 
                            range=(location.get("startLine"), location.get("endLine")), 
                            code_element_type=location.get("codeElementType"), 
                            code_element=location.get("codeElement")
                        )
                    refactoring_instances.append(refactoring_instance)
                
                self.refactorings[commit_hash] = refactoring_instances
    
    @log_execution     
    def calculate_smells_lifespan(self):
        sorted_active_commits = sorted(self.active_commits, key=lambda x: x[1])
        live_smells = {}
        
        previous_commit = None
        for commit_hash, commit_datetime in sorted_active_commits:
            if previous_commit:
                for smell_dict in [self.architecture_smells, self.design_smells, self.implementation_smells, self.testability_smells, self.test_smells]:
                    smell_dict: dict[str, list]
                    added_smells = set()
                    removed_smells = set()
                    previous_smells = smell_dict.get(previous_commit, [])
                    current_smells = smell_dict.get(commit_hash, [])
                    
                    previous_smells_set = set(previous_smells)
                    current_smells_set = set(current_smells)
                    added_smells = current_smells_set - previous_smells_set
                    removed_smells = previous_smells_set - current_smells_set
                        
                    for smell in added_smells:
                        smell_inst = SmellInstance(smell)
                        smell_inst.introduced_at(commit_hash, commit_datetime)
                        live_smells[hash(smell_inst.smell)] = smell_inst
                        
                    for smell in removed_smells:
                        smell_hash = hash(smell)
                        if smell_hash in live_smells:
                            live_smells[smell_hash].removed_at(commit_hash, commit_datetime)
                            self.smells_lib.append(live_smells[smell_hash])
                            del live_smells[smell_hash]
            else:
                for smell_dict in [self.architecture_smells, self.design_smells, self.implementation_smells, self.testability_smells, self.test_smells]:
                    current_smells = smell_dict.get(commit_hash, [])
                    
                    for smell in current_smells:
                        smell_inst = SmellInstance(smell)
                        smell_inst.introduced_at(commit_hash, commit_datetime)
                        live_smells[hash(smell)] = smell_inst
            
            previous_commit = commit_hash
            
        for smell in live_smells.values():
            self.smells_lib.append(smell_inst)
        
        # NOTE: optional sorting by introduced date
        self.smells_lib.sort(key=lambda x: x.introduced.datetime)
        
        self._calculate_lifespan_gap()
        self._calc_smell_range()
    
    @log_execution
    def _calculate_lifespan_gap(self):
        for smell in self.smells_lib:
            if smell.introduced and smell.removed:
                if smell.introduced.datetime and smell.removed.datetime:
                    smell.days_span = (smell.removed.datetime - smell.introduced.datetime).days
                    introduced_index = next(i for i, (ch, _) in enumerate(self.all_commits) if ch == smell.introduced.commit_hash)
                    removed_index = next(i for i, (ch, _) in enumerate(self.all_commits) if ch == smell.removed.commit_hash)
                    smell.commit_span =  introduced_index - removed_index
                    
    @log_execution
    def _calc_smell_range(self):
        # pydriller missing nested methods
        
        commits_to_cover = [commit[0] for commit in self.active_commits]
        methods_data_map: dict[str, dict] = PyDriller.get_methods_map(self.repo_path, self.branch, commits_to_cover)
        
        for smell_instance in self.smells_lib:
            if isinstance(smell_instance.smell, (ImplementationSmell, TestSmell)):
                smell_method_name = smell_instance.smell.method_name
            else:
                smell_method_name = None
            
            for file_path, methods_data in methods_data_map.get(smell_instance.introduced.commit_hash, {}).items():
                file_path: str
                methods_data: dict
                if file_path and self._check_file_intersection(smell_instance.smell, target_path=file_path):
                    for method_name, method_range in methods_data.items():
                        method_name: str
                        method_range: tuple
                        method_name_split = method_name.split('::')
                        if smell_method_name in method_name_split:
                            smell_instance.smell.range = method_range
                            break
        
    @log_execution
    def map_refactorings_to_smells(self):
        for smell_instance in self.smells_lib:
            smell_instance.removed_by_refactorings = []
            smell_instance.introduced_by_refactorings = []
            
            for commit_hash, refs_list in self.refactorings.items():
                if smell_instance.introduced: # current version refactorings
                    if commit_hash == smell_instance.introduced.commit_hash:
                        for ref in refs_list:
                            ref_change_pairs = []
                            for change in ref.changes:
                                if change.file_path and self._check_file_intersection(smell_instance.smell, target_path=change.file_path):
                                    if not hasattr(smell_instance.smell, "range") or smell_instance.smell.range is None:
                                        ref_change_pairs.append(change)
                                    else:
                                        if self._check_smell_ref_intersection(smell_instance.smell.range, change.range):
                                            ref_change_pairs.append(change)
                            if ref_change_pairs:
                                new_ref = Refactoring(ref.url, ref.type_name, ref.commit_hash)
                                new_ref.changes = ref_change_pairs
                                smell_instance.introduced_by_refactorings.append(new_ref)
                            break
                
                if smell_instance.removed:        
                    if commit_hash == smell_instance.removed.commit_hash:
                        for ref in refs_list: # current version refactorings
                            for change in ref.changes:
                                ref_change_pairs = []
                                if change.file_path and self._check_file_intersection(smell_instance.smell, target_path=change.file_path):
                                    if not hasattr(smell_instance.smell, "range") or smell_instance.smell.range is None:
                                        ref_change_pairs.append(ref)
                                    else:
                                        if self._check_smell_ref_intersection(smell_instance.smell.range, change.range):
                                            ref_change_pairs.append(ref)
                            if ref_change_pairs:
                                new_ref = Refactoring(ref.url, ref.type_name, ref.commit_hash)
                                new_ref.changes = ref_change_pairs
                                smell_instance.removed_by_refactorings.append(new_ref)          
                            break
    
    def _check_file_intersection(self, smell, target_path: str):
        """
        Check if the smell file path intersects with the target path.
        """
        is_intersected = False
        slash_pkg_path = smell.package_name.replace('.', '/') if hasattr(smell, 'package_name') and smell.package_name else None
        extension = f"{smell.type_name}.java" if hasattr(smell, 'type_name') and smell.type_name else None
        
        if slash_pkg_path:
            if extension:
                if target_path.endswith(f"{slash_pkg_path}/{extension}"):
                    is_intersected = True
            else:
                if slash_pkg_path == "<All packages>":
                    is_intersected = True
                else:
                    target_pkg_path = '/'.join(target_path.split('/')[:-1])
                    target_extension = target_path.split('.')[-1]
                    if target_pkg_path and target_extension:
                        if target_pkg_path.endswith(slash_pkg_path) and target_extension == "java":
                            is_intersected = True
        else:
            print(ColoredStr.orange(f"Invalid input: 'Package Name' and 'Type Name' is missing."))
            
        return is_intersected
                
    def _check_smell_ref_intersection(self, smell_range: tuple[int, int], refactoring_range: tuple[int, int]):
        """
        Check if the smell range intersects with the refactoring range.
        """
        return not (smell_range[1] < refactoring_range[0] or refactoring_range[1] < smell_range[0])

    @log_execution
    def generate_metadata(self):
        for smell_instance in self.smells_lib:
            kind = smell_instance.smell.kind
            smell_name = smell_instance.smell.smell_name
            if kind not in self.present_smell_types:
                self.present_smell_types[kind] = []
            if smell_name not in self.present_smell_types[kind]:
                self.present_smell_types[kind].append(smell_name)

            for ref in smell_instance.removed_by_refactorings:
                ref_type = ref.type_name
                if ref_type not in self.present_refactoring_types:
                    self.present_refactoring_types.append(ref_type)

    @log_execution
    def save_lifespan_to_json(self, username, repo_name):
        relative_repo_path = os.path.relpath(self.repo_path, start=config.ROOT_PATH)
        data = {
            "metadata": {
            "path": relative_repo_path,
            "branch": self.branch,
            "smell_types": self.present_smell_types,
            "refactoring_types": self.present_refactoring_types
            },
            "smell_instances": [smell_instance.to_dict() for smell_instance in self.smells_lib]
        }
        save_json_file(
            file_path=os.path.join(config.SMELL_LIFESPANS_PATH, f"{repo_name}@{username}.json"), 
            data=data
        )