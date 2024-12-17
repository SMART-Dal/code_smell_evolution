from pathlib import Path
import subprocess
import os
import sys
import config
from pydriller import Repository
from utils import GitManager, log_execution, ColoredStr

class Designite:
    jar_path = os.path.join(config.EXECUTABLES_PATH, "DesigniteJava.jar")
    output_dir = os.path.join(config.OUTPUT_PATH, "Designite_OP")

    def __init__(self) -> None:
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
    @log_execution
    def analyze_commits(self, repo_path: Path, branch: str):
        try:
            print(f"\nRepo: {ColoredStr.blue(repo_path)} | Branch: {ColoredStr.green(branch)}")
            branch_ref = branch if branch in ["master", "main"] else "refs/heads/" + branch
            process = subprocess.Popen([
                "java", "-jar", self.jar_path, 
                "-i", repo_path, 
                "-o", os.path.join(self.output_dir, GitManager.get_repo_name(repo_path)), 
                "-ac", branch_ref
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Stream the output line by line
            for line in process.stdout:
                print(line, end="")  # Output JAR stdout in real-time
            for line in process.stderr:
                print(line, end="")  # Output JAR stderr in real-time
            process.wait()
            if process.returncode != 0:
                print(ColoredStr.red(f"Process failed with return code: {process.returncode}"))
        except Exception as e:
            print(ColoredStr.red(f"An error occurred: {e}"))
        
        
class RefMiner:
    bin_path = os.path.join(config.EXECUTABLES_PATH, "RefactoringMiner-3.0.9", "bin")
    output_dir = os.path.join(config.OUTPUT_PATH, "RefMiner_OP")
    
    def __init__(self) -> None:
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
    @log_execution
    def analyze(self, repo_path: Path, branch: str):
        try:
            output_path = os.path.join(self.output_dir, GitManager.get_repo_name(repo_path)+".json")

            try:
                java_proc = subprocess.run(["java","-version"], capture_output=True, shell=False)
                java_proc.check_returncode()
            except Exception as ex:
                print("Java error")
                print(ex)
            os.chdir(self.bin_path)
            
            shell = sys.platform != 'linux'
            
            try:
                print(f"\nRepo: {ColoredStr.blue(repo_path)} | Branch: {ColoredStr.green(branch)}")
                process = subprocess.Popen([
                    "sh","RefactoringMiner",
                    "-a", repo_path, branch,
                    "-json", output_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=shell)
                
                # Stream output in real-time
                for line in process.stdout:
                    print(line, end="")
                for line in process.stderr:
                    print(line, end="")
                process.wait()  # Wait for process to complete
                if process.returncode != 0:
                    print(ColoredStr.red(f"Process failed with return code: {process.returncode}"))
            except Exception as e:
                print(ColoredStr.red(f"An error occurred during analysis: {e}"))
                
        except Exception as e:
            print(ColoredStr.red(f"An error occurred: {e}"))
        
class PyDriller:
    
    @staticmethod
    def get_methods_map(repo_path, branch, commits):
        map = {}
        for commit in Repository(path_to_repo=repo_path, only_in_branch=branch, only_commits=commits, only_modifications_with_file_types=['.java']).traverse_commits():
            file_map = {}
            for file in commit.modified_files:
                methods_data_map = {}
                for m in file.methods:
                    if m.name is not None:
                        methods_data_map[m.name] = (m.start_line, m.end_line)
                file_map[file.new_path] = methods_data_map
            map[commit.hash] = file_map
        return map