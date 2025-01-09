from pathlib import Path
import subprocess
import os
import sys
import config
from pydriller import Repository
from utils import log_execution, ColoredStr

class Designite:
    jar_path = os.path.join(config.EXECUTABLES_PATH, "DesigniteJava.jar")
    output_dir = os.path.join(config.OUTPUT_PATH, "Designite_OP")

    def __init__(self, print_log = False) -> None:
        self.logs = print_log
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
    @log_execution
    def analyze_commits(self, username: str, repo_name: str, repo_path: Path, branch: str):
        try:
            print(f"\nRepo: {ColoredStr.blue(repo_path)} | Branch: {ColoredStr.green(branch)}")
            branch_ref = branch if branch in ["master", "main"] else "refs/heads/" + branch
            output_path = os.path.join(self.output_dir, username, repo_name)
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            
            process = subprocess.Popen([
                "java", "-jar", self.jar_path, 
                "-i", repo_path, 
                "-o", output_path, 
                "-aco", branch_ref
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Stream the output line by line
            for line in process.stdout:
                if self.logs: print(line, end="")  # Output JAR stdout in real-time
            for line in process.stderr:
                print(line, end="")  # Output JAR stderr in real-time
            process.wait()
            if process.returncode != 0:
                print(ColoredStr.red(f"Process failed with return code: {process.returncode}"))
            return process.returncode
        except Exception as e:
            print(ColoredStr.red(f"An error occurred: {e}"))
            return -1
            
    def save_info(self, repo_path: Path, branch: str, success: bool):
        info_file = os.path.join(self.output_dir, "designite_info.txt")
        
        file_exists = os.path.exists(info_file)
        with open(info_file, "a") as f:
            if not file_exists:
                # Write header row if file doesn't exist
                f.write("Repo Path,Branch,Success\n")
            
            # Append the new row of data
            f.write(f"{repo_path},{branch},{success}\n")
        
        
class RefMiner:
    bin_path = os.path.join(config.EXECUTABLES_PATH, "RefactoringMiner-3.0.9", "bin")
    output_dir = os.path.join(config.OUTPUT_PATH, "RefMiner_OP")
    
    def __init__(self, print_log = False) -> None:
        self.logs = print_log
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
    @log_execution
    def analyze(self, username: str, repo_name: str, repo_path: Path, branch: str):
        try:
            output_path = os.path.join(self.output_dir, username, f"{repo_name}.json")

            try:
                java_proc = subprocess.run(["java", "-version"], capture_output=True, shell=False)
                java_proc.check_returncode()
            except Exception as ex:
                print("Java error")
                print(ex)
            os.chdir(self.bin_path)
            
            shell = sys.platform != 'linux'
            
            try:
                print(f"\nRepo: {ColoredStr.blue(repo_path)} | Branch: {ColoredStr.green(branch)}")
                result = subprocess.run([
                    "sh", "RefactoringMiner",
                    "-a", repo_path, branch,
                    "-json", output_path
                ], capture_output=True, text=True, shell=shell)
                
                if result.returncode != 0:
                    print(ColoredStr.red(f"Process failed with return code: {result.returncode}"))
                    print(result.stderr)
                    
                if self.logs:
                    print(result.stdout)
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