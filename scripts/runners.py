from pathlib import Path
import subprocess
import os
import sys
import config
from utils import GitManager, ProcessSpinner

class Designite:
    jar_path = os.path.join(config.EXECUTABLES_PATH, "DesigniteJava.jar")
    output_dir = os.path.join(config.OUTPUT_PATH, "Designite_OP")

    def __init__(self) -> None:
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
    def analyze_commits(self, repo_path: Path, branch: str):
        with ProcessSpinner("Calculating code smells with Designite for repo " + GitManager.get_repo_name(repo_path)): 
            try:
                result = subprocess.run([
                    "java", "-jar", self.jar_path, 
                    "-i", repo_path, 
                    "-o", os.path.join(self.output_dir, GitManager.get_repo_name(repo_path)), 
                    "-ac", branch
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                error = result.stderr.decode() if result.stderr else "No error message"
            except subprocess.CalledProcessError as e:
                output = e.stdout.decode()
                error = e.stderr.decode() if e.stderr else "No error message"
        
        
class RefMiner:
    def __init__(self) -> None:
        self.bin_path = os.path.join(config.EXECUTABLES_PATH, "RefactoringMiner-3.0.9", "bin")
        self.output_dir = os.path.join(config.OUTPUT_PATH, "RefMiner_OP")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
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
            
            with ProcessSpinner("Analyzing repository with RefactoringMiner for repo " + GitManager.get_repo_name(repo_path)):
                try:
                    result = subprocess.run([
                    "sh","RefactoringMiner",
                    "-a", repo_path,
                    "-json", output_path
                ], check=True, capture_output=True, shell=shell)
                    output = result.stdout.decode()
                    error = result.stderr.decode()
                except subprocess.CalledProcessError as e:
                    output = e.stdout.decode()
                    error = e.stderr.decode()
                    print(f"Error: {error}")
            
            os.chdir(config.ROOT_PATH)
        except Exception as e:
            print(f"An error occurred: {e}")
            return None