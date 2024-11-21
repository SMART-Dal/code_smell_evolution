import os
import sys
import itertools
import time
import threading
import json
import csv
from git import Repo

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
    for root, dirs, _ in os.walk(dir_path):
        for name in dirs:
            yield os.path.join(root, name)

class GitManager:
    BASE_URL = "https://github.com/"
    
    @staticmethod
    def clone_repo(repo_path, repo_full_name):
        """
        Clone a Git repository.

        :param repo_full_name: The full name of the repository in the format "username/repo_name".
        :param repo_path: Path to the local Git repository.
        """
        repo_url = GitManager.BASE_URL + repo_full_name + ".git"
        with ProcessSpinner(f"Cloning repository {repo_full_name}"):
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
    def get_git_branches(repo_path):
        """
        Get a list of branches in a Git repository.

        :param repo_path: Path to the local Git repository.
        :return: A list of branch names.
        """
        branches = []
        try:
            repo = Repo(repo_path)
            branches = [head.name for head in repo.heads]
        except Exception as e:
            print(f"An error occurred: {e}")
        return branches
    
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
    
class ProcessSpinner:
    def __init__(self, message):
        self.message = message
        self.spinner = itertools.cycle(['-', '/', '|', '\\'])
        self.stop_running = False
        self.success = None

    def spinner_task(self):
        while not self.stop_running:
            sys.stdout.write(f"\r{next(self.spinner)} {self.message}")
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self):
        self.stop_running = False
        threading.Thread(target=self.spinner_task, daemon=True).start()

    def stop(self, success=True):
        self.stop_running = True
        self.success = success
        sys.stdout.write('\r')
        sys.stdout.flush()
        if self.success:
            sys.stdout.write(f"\r✔ {self.message} - Completed\n")
        else:
            sys.stdout.write(f"\r✖ {self.message} - Failed\n")
        sys.stdout.flush()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop(success=(exc_type is None))
        return False