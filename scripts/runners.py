from pathlib import Path
import subprocess
import os
import sys
import config
from pydriller import Repository
from utils import GitManager, log_execution

class Designite:
    jar_path = os.path.join(config.EXECUTABLES_PATH, "DesigniteJava.jar")
    output_dir = os.path.join(config.OUTPUT_PATH, "Designite_OP")

    def __init__(self) -> None:
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
    @log_execution
    def analyze_commits(self, repo_path: Path, branch: str):
        try:
            print(f"Repo: {repo_path}")
            result = subprocess.run([
                "java", "-jar", self.jar_path, 
                "-i", repo_path, 
                "-o", os.path.join(self.output_dir, GitManager.get_repo_name(repo_path)), 
                "-ac", branch
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            error = result.stderr.decode()
        except subprocess.CalledProcessError as e:
            error = e.stderr.decode()
            print(f"Error: {error}")
        
        
class RefMiner:
    bin_path = os.path.join(config.EXECUTABLES_PATH, "RefactoringMiner-3.0.9", "bin")
    output_dir = os.path.join(config.OUTPUT_PATH, "RefMiner_OP")
    
    def __init__(self) -> None:
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
    @log_execution
    def analyze(self, repo_path: Path, output_path: Path):
        try:
            if not os.path.exists(output_path):
                os.mkdir(output_path)

            output_path = os.path.join(self.output_dir, GitManager.get_repo_name(repo_path)+".json")

            try:
                java_proc = subprocess.run(["java","-version"], capture_output=True, shell=False)
                java_proc.check_returncode()
            except Exception as ex:
                print("Java error")
                print(ex)
            os.chdir(self.bin_path)
            
            shell = True
            if sys.platform == 'linux':
                shell = False
            
            try:
                print(f"Repo: {repo_path}")
                result = subprocess.run([
                    "sh","RefactoringMiner",
                    "-a", repo_path,
                    "-json", output_path
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                error = result.stderr.decode()
            except subprocess.CalledProcessError as e:
                error = e.stderr.decode()
                print(f"Error: {error}")
            
            os.chdir(config.ROOT_PATH)
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        
class PyDriller:
    
    @staticmethod
    def get_methods_map(repo_path, branch, commit_hash):
        file_method_data_map = {}
        for commit in Repository(path_to_repo=repo_path, only_in_branch=branch, only_commits=[commit_hash], only_modifications_with_file_types=['.java']).traverse_commits():
            for file in commit.modified_files:
                methods_data_map = {}
                for m in file.methods:
                    if m.name is not None:
                        methods_data_map[m.name] = (m.start_line, m.end_line)
                file_method_data_map[file.new_path] = methods_data_map
        return file_method_data_map