from pathlib import Path
import subprocess
import os
import sys
import config
from utils import get_repo_name

class Designite:
    def __init__(self) -> None:
        self.jar_path = os.path.join(config.EXECUTABLES_PATH, "DesigniteJava.jar")
        self.output_dir = os.path.join(config.OUTPUT_PATH, "Designite_OP")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
    def analyze_commits(self, repo_path: Path, branch: str):
        
        subprocess.run([
            "java", "-jar", self.jar_path, 
            "-i", repo_path, 
            "-o", os.path.join(self.output_dir, get_repo_name(repo_path)), 
            "-ac", branch
        ])
        
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

            output_path = os.path.join(self.output_dir, get_repo_name(repo_path)+".json")

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
            
            ref_exec = subprocess.run([
                "sh","RefactoringMiner",
                "-a", repo_path,
                "-json", output_path
            ], capture_output=True, shell=shell)
            ref_exec.check_returncode()
            
            os.chdir(config.ROOT_PATH)
            

        except subprocess.CalledProcessError as error:
            print(ref_exec.stdout)
            print(error)
            os.chdir(config.ROOT_PATH)
            raise Exception("Error running RefactoringMiner in repository (CSP) - "+repo_path)
        except Exception as e:
            print(e)
            os.chdir(config.ROOT_PATH)
            raise Exception("Error running RefactoringMiner in repository - "+repo_path)