import os
import json
import csv
import subprocess
import traceback
from git import Repo

def log_execution(func):
    def wrapper(*args, **kwargs):
        # Determine class name if the function is a method
        class_name = None
        if args:
            class_name = args[0].__class__.__name__ if hasattr(args[0], "__class__") else None
            
        if class_name == "Designite":
            class_name = ColoredStr.orange(class_name)
        elif class_name == "RefMiner":
            class_name = ColoredStr.cyan(class_name)

        # Log the custom message and function execution details
        if class_name:
            print(ColoredStr.light_gray(f"▶ Starting execution of {class_name}.{func.__name__}"))
        else:
            print(ColoredStr.light_gray(f"▶ Starting execution of {func.__name__}"))

        try:
            result = func(*args, **kwargs)
            if class_name:
                print(ColoredStr.light_gray(f"✔ Finished execution of {class_name}.{func.__name__}"))
            else:
                print(ColoredStr.light_gray(f"✔ Finished execution of {func.__name__}"))
            return result
        except Exception as e:
            if class_name:
                print(ColoredStr.red(f"✖ Error occurred in {class_name}.{func.__name__}: {e}"))
            else:
                print(ColoredStr.red(f"✖ Error occurred in {func.__name__}: {e}"))
                
            # Log the full error traceback
            traceback_str = traceback.format_exc()
            print(f"Traceback: {traceback_str}")
            raise
    return wrapper

class ColoredStr:
    @staticmethod
    def blue(string): return "\033[94m {}\033[00m" .format(string)
    
    @staticmethod
    def green(string): return "\033[92m {}\033[00m" .format(string)
    
    @staticmethod
    def red(string): return "\033[91m {}\033[00m" .format(string)

    @staticmethod
    def light_gray(string): return "\033[97m {}\033[00m" .format(string)
    
    @staticmethod
    def orange(string): return "\033[93m {}\033[00m" .format(string)
    
    @staticmethod
    def cyan(string): return "\033[96m {}\033[00m" .format(string)

def load_json_file(file_path):
    """
    Load a JSON file.

    :param file_path: Path to the JSON file.
    :return: The JSON data.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def save_json_file(file_path, data):
    """
    Save data to a JSON file. If the directory does not exist, create it.

    :param file_path: Path to the JSON file.
    :param data: Data to be saved.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def load_csv_file(file_path, skipCols=[]):
    """
    Load a CSV file and return its contents as a list of dictionaries, skipping specified columns.

    :param file_path: Path to the CSV file.
    :param skipCols: List of column names to skip.
    :return: List of dictionaries containing the CSV data.
    """
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        data = [{k: v for k, v in row.items() if k not in skipCols} for row in reader]
    return data

def traverse_directory(dir_path):
    """
    Traverse a directory and yield all files and subdirectories.
    
    :param dir_path: Path to the directory.
    :yield: Paths of files and subdirectories.
    """
    for root, dirs, files in os.walk(dir_path):
        for name in dirs:
            yield os.path.join(root, name)
        for name in files:
            yield os.path.join(root, name)

def get_smell_dict(smell_str: str) -> dict:
    return eval(smell_str)

class GitManager:
    BASE_URL = "https://github.com/"
    
    @staticmethod
    @log_execution
    def clone_repo(repo_path, repo_full_name):
        """
        Clone a Git repository.

        :param repo_full_name: The full name of the repository in the format "username/repo_name".
        :param repo_path: Path to the local Git repository.
        """
        repo_url = GitManager.BASE_URL + repo_full_name + ".git"
        try:
            Repo.clone_from(repo_url, repo_path)
        except Exception as e:
            print(f"An error occurred while cloning repo: {repo_full_name}")
            print(f"Error: {e}")
            
    @staticmethod
    def get_repo_name(repo_path):
        """
        Get the name of the repository folder.

        :param repo_path: Path to the local Git repository.
        :return: The name of the repository folder.
        """
        return os.path.basename(os.path.normpath(repo_path))
    
    @staticmethod
    def get_default_branch(repo_path):
        """
        Get the default branch in a Git repository.

        :param repo_path: Path to the local Git repository.
        :return: The name of the default branch.
        """
        default_branch = None
        try:
            repo = Repo(repo_path)
            if repo.head.is_detached:
                default_branch = repo.git.symbolic_ref('refs/remotes/origin/HEAD').split('/')[-1]
            else:
                default_branch = repo.head.ref.name
        except Exception as e:
            print(f"An error occurred: {e}")
        return default_branch
    
    @staticmethod
    def get_all_commits(repo_path, branch):
        """
        Get all commits in a Git repository.

        :param repo_path: Path to the local Git repository.
        :param branch: Branch name.
        :return: A list of commit objects.
        """
        repo = Repo(repo_path)
        commits = list(repo.iter_commits(branch))
        return [(commit.hexsha, commit.committed_datetime) for commit in commits]
    
    @staticmethod
    def checkout_repo(repo_path, commit_hash) -> bool:
        try:
            subprocess.run(["git", "checkout", commit_hash], cwd=repo_path)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error git checkout for repo - {repo_path}, commit - {commit_hash}: Error: {e.stderr}")
            return False