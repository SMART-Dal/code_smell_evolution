import os
import shutil
import re
from datetime import datetime
from runners import Designite, RefMiner
import config
from utils import GitManager, GitUtils, FileUtils
from utils import log_execution
from models import SmellInstance, Smell, Refactoring, CommitInfo, DESIGN_SMELL, IMP_SMELL
from zip import unzip_file

class RepoDataAnalyzer:
    def __init__(self, username: str, repo_name: str, repo_path: str, branch: str):
        self.slurm_dir = os.environ.get("SLURM_TMPDIR", None)
        if self.slurm_dir is None:
            raise RuntimeError("No slurm tmp dir available")
        
        self.repo_path = repo_path
        self.repo_designite_output_path = os.path.join(self.slurm_dir, "output", "Designite_OP", username, repo_name)
        self.repo_refminer_output_path = os.path.join(RefMiner.output_dir, username, f"{repo_name}.json")
        
        self.repo_stats = {}
        
        self.branch = branch
        self.active_commits: list[tuple[str, datetime]] = []
        self.all_commits: list[tuple[str, datetime]] = GitManager.get_all_commits(repo_path, branch)
        self.smells: dict[str, list[Smell]] = {}                # smells dictionary for each commit
        self.refactorings: dict[str, list[Refactoring]] = {}    # refactorings dictionary for each commit
        
        self.pairs_lib: list[SmellInstance] = []               # list of smell instances mapped to refactorings
        self.unmapped_refactorings: list[Refactoring] = []     # list of refactorings that are not mapped to any smell instance
        
        # metadata
        self.present_smell_types = {}
        self.present_refactoring_types = []
        
    @log_execution
    def setup_repo_dataset(self, idx, username, repo_name):
        
        if not os.path.exists(config.ZIP_LIB):
            raise RuntimeError(f"ZIP_LIB directory not found: {config.ZIP_LIB}")
        
        # Smells dataset setup
        try:
            SMELLS_DIR = os.path.join(self.slurm_dir, "output", "Designite_OP",  username, repo_name)
            if os.path.exists(SMELLS_DIR):
                shutil.rmtree(SMELLS_DIR)
                
            os.makedirs(SMELLS_DIR)

            target_dir = os.path.join(self.slurm_dir, "output", "Designite_OP",  username, repo_name)
            unzip_file(os.path.join(config.ZIP_LIB, f'smells_{idx}.zip'), target_dir)
        except Exception as e:
            raise RuntimeError(f"Failed to set up smells dataset for {username}/{repo_name}: {e}")
        
        # Refactoring dataset setup
        try:
            REFS_DIR = os.path.join(RefMiner.output_dir, username)
            if not os.path.exists(REFS_DIR):
                os.makedirs(REFS_DIR)
                
            target_dir = os.path.join(RefMiner.output_dir, username)
            unzip_file(os.path.join(config.ZIP_LIB, f'refs_{idx}.zip'), target_dir)
        except Exception as e:
            raise RuntimeError(f"Failed to set up refactoring dataset for {username}/{repo_name}: {e}")
        
    @log_execution
    def flush_repo_dataset(self):
        # Smells dataset cleanup
        try:
            if os.path.exists(self.repo_designite_output_path):
                shutil.rmtree(self.repo_designite_output_path)
                print(f"Flushed smells dataset directory: {self.repo_designite_output_path}")
            else:
                print(f"Smells dataset directory not found for cleanup: {self.repo_designite_output_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to flush smells dataset: {e}")
    
        # Refactoring dataset cleanup
        try:
            if os.path.exists(self.repo_refminer_output_path):
                if os.path.isdir(self.repo_refminer_output_path):
                    shutil.rmtree(self.repo_refminer_output_path)
                    print(f"Flushed refactoring dataset directory: {self.repo_refminer_output_path}")
                else:
                    os.remove(self.repo_refminer_output_path)
                    print(f"Flushed refactoring dataset file: {self.repo_refminer_output_path}")
            else:
                print(f"Refactoring dataset path not found for cleanup: {self.repo_refminer_output_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to flush refactoring dataset: {e}")
        
    @log_execution
    def load_raw_smells(self):
        """
        Load raw smells from Designite output.
        Will load smells for active commits only.
        """
        designite_stats = {
            "smells_collected": {
                "total_smells": 0,
                "total_design_smells": 0,
                "total_imp_smells": 0,
                DESIGN_SMELL: {}, 
                IMP_SMELL: {}
            },
            "commits_analyzed": {
                "total": 0,
                "hashes": []
            }
        }
        
        for commit_path in FileUtils.traverse_directory(self.repo_designite_output_path):
            commit_hash = os.path.basename(commit_path)
            if commit_hash.endswith('.csv'):
                continue
            
            designite_stats["commits_analyzed"]["hashes"].append(commit_hash)
            designite_stats["commits_analyzed"]["total"] += 1
            commit_datetime = next((dt for ch, dt in self.all_commits if ch == commit_hash), None)
            if commit_datetime:
                self.active_commits.append((commit_hash, commit_datetime))
            
            for csv in ["DesignSmells.csv", "ImplementationSmells.csv"]:
                csv_path = os.path.join(commit_path, csv)
                smell_kind = self._get_smell_kind(csv)
                if os.path.exists(csv_path):
                    smell_instances = []
                    smell_hashes = set()
                    
                    smells_data = FileUtils.load_csv_file(csv_path, skipCols=config.SMELL_SKIP_COLS)
                    for smell_row in smells_data:
                        package_name = smell_row.get("Package Name", None)
                        type_name = smell_row.get("Type Name", None)
                        method_name = smell_row.get("Method Name", None)
                        method_start_line = smell_row.get("Method start line no", None)
                        smell_name = smell_row.get(f"{smell_kind} Smell", None)
                        designite_stats["smells_collected"][smell_kind][smell_name] = designite_stats["smells_collected"][smell_kind].get(smell_name, 0) + 1
                        
                        # cause = smell_row.get("Cause of the Smell", None)
                        
                        smell_instance = Smell(package_name, smell_kind, smell_name)
                        smell_instance.type_name = type_name
                        smell_instance.method_name = method_name
                        smell_instance.method_start_ln = int(method_start_line) if method_start_line else None
                        
                        if smell_instance.full_hash() in smell_hashes: # to remove duplicates
                            continue
                        
                        smell_instances.append(smell_instance)
                        smell_hashes.add(smell_instance.full_hash())
                    
                    if commit_hash not in self.smells:
                        self.smells[commit_hash] = []
                    self.smells[commit_hash].extend(smell_instances)

        designite_stats["smells_collected"]["total_design_smells"] = sum(designite_stats["smells_collected"][DESIGN_SMELL].values())
        designite_stats["smells_collected"]["total_imp_smells"] = sum(designite_stats["smells_collected"][IMP_SMELL].values())
        designite_stats["smells_collected"]["total_smells"] = (
            designite_stats["smells_collected"]["total_design_smells"] +
            designite_stats["smells_collected"]["total_imp_smells"]
        )
        designite_stats["commits_analyzed"]["total"] = len(designite_stats["commits_analyzed"]["hashes"])
    
        self.repo_stats["designite_stats"] = designite_stats
                    
    def _get_smell_kind(self, csv_name):
        match = re.match(r"(\w+)Smells\.csv", csv_name)
        if match:
            return match.group(1)
        else:
            raise ValueError(f"Invalid smell csv name: {csv_name}")
    
    @log_execution
    def calculate_smells_lifespan(self):
        sorted_active_commits = sorted(self.active_commits, key=lambda x: x[1])
        live_smells: dict[int, SmellInstance] = {}
        
        previous_commit = None
        for curr_commit, curr_commit_datetime in sorted_active_commits:
            added_smells: list[Smell] = []
            removed_smells: list[Smell] = []
            
            if previous_commit:
                 # Get smells from the previous and current commit for comparison
                prev_smells = self.smells.get(previous_commit, [])
                curr_smells = self.smells.get(curr_commit, [])
                prev_smell_hashes = {smell.hash(): smell for smell in prev_smells}
                curr_smell_hashes = {smell.hash(): smell for smell in curr_smells}
                
                # Find added smells
                for curr_smell_hash, curr_smell in curr_smell_hashes.items():
                    if curr_smell_hash not in prev_smell_hashes:
                        added_smells.append(curr_smell)
                    else:
                        prev_smell = prev_smell_hashes[curr_smell_hash]
                        if curr_smell.smell_kind == IMP_SMELL and prev_smell.smell_kind == IMP_SMELL:
                            # Check if the smell has moved
                            if curr_smell.method_start_ln != prev_smell.method_start_ln:
                                live_smells[curr_smell_hash].add_new_version(
                                    changed_method_start_ln=curr_smell.method_start_ln, 
                                    commit_info=CommitInfo(curr_commit, curr_commit_datetime)
                                )

                # Find removed smells
                for prev_smell_hash, prev_smell in prev_smell_hashes.items():
                    if prev_smell_hash not in curr_smell_hashes:
                        removed_smells.append(prev_smell)
                
            else:       # Handle the first commit, where there is no previous commit for comparison
                added_smells = self.smells.get(curr_commit, [])
            
            # Add new added smells to live_smells
            for smell in added_smells:
                smell_inst = SmellInstance(smell, CommitInfo(curr_commit, curr_commit_datetime))
                live_smells[smell_inst.latest_smell().hash()] = smell_inst
                
            # Pop removed smells from live_smells
            for smell in removed_smells:
                if smell.hash() in live_smells:
                    smell_inst = live_smells[smell.hash()]
                    smell_inst.add_removed_version(CommitInfo(curr_commit, curr_commit_datetime))
                    smell_inst.is_alive = False
                    self.pairs_lib.append(smell_inst)
                    live_smells.pop(smell_inst.latest_smell().hash())

            previous_commit = curr_commit
            
        # Handle any remaining live smells (probably never removed)
        for _, smell_inst in live_smells.items():
            self.pairs_lib.append(smell_inst)
            
        # NOTE: optional sorting by introduced date
        self.pairs_lib.sort(key=lambda x: x.versions[0].datetime)
        
        self._calculate_lifespan_gap()
        self._calculate_smell_methods_end_line()
    
    @log_execution
    def _calculate_lifespan_gap(self):
        for smell_instance in self.pairs_lib:
            if not smell_instance.is_alive:
                smell_instance.days_span = (smell_instance.versions[-1].datetime - smell_instance.versions[0].datetime).days
                introduced_index = next(i for i, (ch, _) in enumerate(self.all_commits) if ch == smell_instance.versions[0].commit_hash)
                removed_index = next(i for i, (ch, _) in enumerate(self.all_commits) if ch == smell_instance.versions[-1].commit_hash)
                commit_span = removed_index - introduced_index
                smell_instance.commit_span = commit_span if commit_span >= 0 else 0
                
    @log_execution
    def _calculate_smell_methods_end_line(self):
        methods_info_map = {}
        
        # collects methods that require end line calculation
        for smell_instance in self.pairs_lib:
            for smell_idx, smell in enumerate(smell_instance.smell_history):
                smell_commit_hash = smell_instance.versions[smell_idx].commit_hash
                file_path = smell_instance.get_file_path()
                if smell.method_start_ln and smell.method_name:
                    if smell_commit_hash not in methods_info_map:
                        methods_info_map[smell_commit_hash] = {}
                    if file_path not in methods_info_map[smell_commit_hash]:
                        methods_info_map[smell_commit_hash][file_path] = {}
                    methods_info_map[smell_commit_hash][file_path][smell.method_name] = [smell.method_start_ln, None]
                    
        # calculates end line for each method
        for commit_hash, methods_data in methods_info_map.items():
            for file_path, methods_data in methods_data.items():
                for method_name, method_range in methods_data.items():
                    method_start_ln = method_range[0]
                    method_end_ln = GitUtils.get_method_end_line_at_commit(self.repo_path, commit_hash, file_path, method_name, method_start_ln)
                    
                    if method_end_ln == -1:
                        # print(ColoredStr.orange(f"Failed to find method_end_ln: {commit_hash} | {file_path} | {method_name}"))
                        method_end_ln = None
                    
                    methods_data[method_name][1] = method_end_ln
                
        # updates smell instances with end line info
        for smell_instance in self.pairs_lib:
            for smell_idx, smell in enumerate(smell_instance.smell_history):
                smell_commit_hash = smell_instance.versions[smell_idx].commit_hash
                file_path = smell_instance.get_file_path()
                if smell.method_start_ln and smell.method_name:
                    method_range = methods_info_map[smell_commit_hash][file_path][smell.method_name]
                    smell_instance.smell_history[smell_idx].method_end_ln = method_range[1] 
        
    @log_execution
    def load_raw_refactorings(self):
        """
        Load raw refactorings from RefMiner output.
        Will load refactorings for active commits only.
        """
        refminer_stats = {
            "total_refactorings": 0,
            "refactoring_types": {},
            "commits_analyzed": {
                "total": 0,
                "hashes": []
            }
        }
        
        for commit in FileUtils.load_json_file(self.repo_refminer_output_path).get("commits"):
            if any(commit.get("sha1") == active_commit[0] for active_commit in self.active_commits):
                commit_hash = commit.get("sha1")
                refs = commit.get("refactorings")
                url = commit.get("url")
                
                refactoring_instances = []
                for ref in refs:
                    refactoring_instance = Refactoring(url, commit_hash, ref.get("type", None), ref.get("description", None))
                    for location in ref.get("leftSideLocations"):
                        refactoring_instance.add_left_change(
                            file_path=location.get("filePath"), 
                            range=(location.get("startLine"), location.get("endLine")), 
                            code_element_type=location.get("codeElementType"), 
                            code_element=location.get("codeElement"),
                            description=location.get("description")
                        )
                    for location in ref.get("rightSideLocations"):
                        refactoring_instance.add_right_change(
                            file_path=location.get("filePath"), 
                            range=(location.get("startLine"), location.get("endLine")), 
                            code_element_type=location.get("codeElementType"), 
                            code_element=location.get("codeElement"),
                            description=location.get("description")
                        )
                    refactoring_instances.append(refactoring_instance)
                    
                    # Update refminer_stats
                    ref_type = ref.get("type", None)
                    if ref_type:
                        refminer_stats["refactoring_types"][ref_type] = refminer_stats["refactoring_types"].get(ref_type, 0) + 1
                        refminer_stats["total_refactorings"] += 1
                
                if commit_hash not in self.refactorings:
                    self.refactorings[commit_hash] = refactoring_instances
                else:
                    self.refactorings[commit_hash].extend(refactoring_instances)
                
                refminer_stats["commits_analyzed"]["hashes"].append(commit_hash)
        
        refminer_stats["commits_analyzed"]["total"] = len(refminer_stats["commits_analyzed"]["hashes"])
        self.repo_stats["refminer_stats"] = refminer_stats
    
    @log_execution
    def map_refactorings_to_smells(self):
        for smell_instance in self.pairs_lib:
            smell_instance.removed_by_refactorings = []
            smell_instance.introduced_by_refactorings = []
            introuced_commit_hash = smell_instance.get_introduced_at()
            removed_commit_hash = smell_instance.get_removed_at()
                
            # Map refactorings that introduced the smell
            refs = self.refactorings.get(introuced_commit_hash, [])
            for ref in refs:
                for rc in ref.right_changes:
                    # check if the smell file path intersects with the refactoring file path
                    if rc.file_path and self._check_file_intersection(smell_instance.get_file_path(), target_path=rc.file_path):
                        if smell_instance.get_smell_kind() == IMP_SMELL:
                            if self._check_smell_ref_intersection(smell_instance.introduced_smell().get_range(), rc.range):
                                ref.is_mapped_to_introduction = True
                                smell_instance.introduced_by_refactorings.append(ref)
                                break
                        else: # for Design smells, no range check in a file
                            ref.is_mapped_to_introduction = True
                            smell_instance.introduced_by_refactorings.append(ref)
                            break
                
            # Map refactorings that removed the smell
            if not smell_instance.is_alive:
                refs = self.refactorings.get(removed_commit_hash, [])
                for ref in refs:
                    for lc in ref.left_changes:
                        if lc.file_path and self._check_file_intersection(smell_instance.get_file_path(), target_path=lc.file_path):
                            if smell_instance.get_smell_kind() == IMP_SMELL:
                                if self._check_smell_ref_intersection(smell_instance.latest_smell().get_range(), lc.range):
                                    ref.is_mapped_to_removal = True
                                    smell_instance.removed_by_refactorings.append(ref)
                                    break
                            else: # for Design smells, no range check in a file
                                ref.is_mapped_to_removal = True
                                smell_instance.removed_by_refactorings.append(ref)
                                break
                                
        # Collect unmapped refactorings
        for _, refs in self.refactorings.items():
            for ref in refs:
                if not ref.is_mapped_to_removal or not ref.is_mapped_to_introduction:
                    self.unmapped_refactorings.append(ref)
    
    def _check_file_intersection(self, smell_file_path, target_path: str):
        """
        Check if the smell file path intersects with the target path.
        """
        is_intersected = False
        
        if smell_file_path == "<All packages>":
            is_intersected = True
        elif target_path.endswith(smell_file_path):
            is_intersected = True
        else:
            target_pkg_path = '/'.join(target_path.split('/')[:-1])
            target_extension = target_path.split('.')[-1]
            if target_pkg_path and target_extension:
                if target_pkg_path.endswith(smell_file_path) and target_extension == "java":
                    is_intersected = True
            
        return is_intersected
                
    def _check_smell_ref_intersection(self, smell_range: tuple[int, int], refactoring_range: tuple[int, int]):
        """
        Check if the smell range intersects with the refactoring range.
        """
        if smell_range == (None, None):
            return False
        
        smell_start, smell_end = smell_range
        ref_start, ref_end = refactoring_range
        
        if smell_end is None:
            return ref_start <= smell_start <= ref_end
        
        return not (smell_end < ref_start or ref_end < smell_start)

    @log_execution
    def save_data_to_json(self, username, repo_name):
        """
        Save the smell lifespan data and its statistics to JSON files.
        """
        
        relative_repo_path = os.path.relpath(self.repo_path, start=config.ROOT_PATH)
        sorted_active_commits = sorted(self.active_commits, key=lambda x: x[1])
        
        # save smell lifespan data
        data = {
            "metadata": {
                "path": relative_repo_path,
                "branch": self.branch,
                "commit_range": {
                    "start": sorted_active_commits[0][0],
                    "end": sorted_active_commits[-1][0]
                },
            },
            "smell_instances": [smell_instance.to_dict() for smell_instance in self.pairs_lib],
            "unmapped_refactorings": [ref.to_dict() for ref in self.unmapped_refactorings]
        }
        FileUtils.save_json_file(
            file_path=os.path.join(config.SMELL_REF_MAP_PATH, f"{repo_name}@{username}.json"), 
            data=data
        )
        
        # save repo stats data
        stats_data = {
            "designite_stats": self.repo_stats.get("designite_stats", None),
            "refminer_stats": self.repo_stats.get("refminer_stats", None)
        }
        FileUtils.save_json_file(
            file_path=os.path.join(config.SMELL_REF_MAP_PATH, f"{repo_name}@{username}.stats.json"), 
            data=stats_data
        )