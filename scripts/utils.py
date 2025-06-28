import os
import re
import json
import csv
import traceback
import hashlib
import chardet
from git import Repo, NULL_TREE

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
    
def hashgen(data: any) -> str:
    """
    Generate an MD5 hash for the given data.

    Args:
        data (any): The input data to hash. Can be of any type (e.g., str, int, tuple).

    Returns:
        str: The hexadecimal representation of the MD5 hash.
    """
    try:
        if not isinstance(data, str):
            data = str(data)
    except RecursionError:
        raise ValueError("Recursive structures detected in data. Please check for self-references.")
    
    # Convert the input data to bytes
    byte_data = data.encode('utf-8')
    
    # Create an MD5 hash object and compute the hash
    md5_hash = hashlib.md5(byte_data)
    
    # Return the hexadecimal representation of the hash
    return md5_hash.hexdigest()

class FileUtils:
    def load_json_file(file_path):
        """
        Load a JSON file.

        :param file_path: Path to the JSON file.
        :return: The JSON data or an empty dictionary if the file is not found.
        """
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        return data

    def save_json_file(file_path, data):
        """
        Save data to a JSON file. If the directory does not exist, create it.

        :param file_path: Path to the JSON file.
        :param data: Data to be saved.
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)

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
            print(f"Cloning repo: {ColoredStr.blue(repo_full_name)}")
            Repo.clone_from(url=repo_url, to_path=repo_path)
        except Exception as e:
            print(f"An error occurred while cloning repo: {ColoredStr.red(repo_full_name)}")
            print(f"Error: {ColoredStr.red(e)}")
    
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
        It will be sorted by commit date in ascending order.

        :param repo_path: Path to the local Git repository.
        :param branch: Branch name.
        :return: A list of commit objects.
        """
        repo = Repo(repo_path)
        commits = list(repo.iter_commits(branch))[::-1]
        commit_pairs = [(commit.hexsha, commit.committed_datetime) for commit in commits]
        commit_pairs.sort(key=lambda x: x[1])
        return commit_pairs
    
    @staticmethod
    def get_file_content_at_commit(repo_path, commit_hash, file_path):
        """
        Get the content of a file at a specific commit.

        :param repo_path: Path to the local Git repository.
        :param commit_hash: Hash of the commit.
        :param file_path: Path to the file.
        :return: The content of the file at the given commit.
        """
        repo = Repo(repo_path)
        commit = repo.commit(commit_hash)
        tree = commit.tree

        # Traverse the tree to find the file with the ending path
        for item in tree.traverse():
            if item.path.endswith(file_path):
                file_bytes = item.data_stream.read()
                detected = chardet.detect(file_bytes)
                encoding = detected["encoding"] if detected["encoding"] else "utf-8"
                file_content = file_bytes.decode(encoding, errors="replace")
                return file_content

        return None
    
    @staticmethod
    def get_changes_at_commit(repo_path, commit_hash):
        """
        Get the changed line numbers for each file in a specific commit.

        :param repo_path: Path to the local Git repository.
        :param commit_hash: Hash of the commit.
        :return: A dict mapping file paths to sets of changed line numbers.
        """
        repo = Repo(repo_path)
        commit = repo.commit(commit_hash)
        parent = commit.parents[0] if commit.parents else None
        changes = {}

        diffs = commit.diff(parent or NULL_TREE, create_patch=True)

        hunk_header_regex = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

        for diff in diffs:
            if not diff.diff:
                continue

            file_path = diff.b_path or diff.a_path
            if not file_path or not file_path.endswith(".java"):
                continue

            ranges = []

            diff_text = diff.diff.decode("utf-8", errors="replace")
            for line in diff_text.splitlines():
                if line.startswith("@@"):
                    match = hunk_header_regex.match(line)
                    if match:
                        start = int(match.group(1))
                        count = int(match.group(2)) if match.group(2) else 1
                        ranges.append((start, start + count - 1))

            if ranges:
                changes[file_path] = ranges

        return changes
    
    @staticmethod
    def get_commit_message(repo_path, commit_hash):
        """
        Get the commit message for a specific commit.

        :param repo_path: Path to the local Git repository.
        :param commit_hash: Hash of the commit.
        :return: The commit message.
        """
        repo = Repo(repo_path)
        commit = repo.commit(commit_hash)
        return commit.message.strip()
    
class GitUtils:
    @staticmethod
    def get_method_end_line_at_commit(repo_path, commit_hash, file_path, method_name, start_line):
        """
        Get the end line number of a method in a Java file at a specific commit.

        :param repo_path: Path to the local Git repository.
        :param commit_hash: Hash of the commit.
        :param file_path: Path to the Java file.
        :param method_name: Name of the method.
        :param start_line: Starting line number of the method.
        :return: End line number of the method. Returns -1 if not found.
        """
        file_content = GitManager.get_file_content_at_commit(repo_path, commit_hash, file_path)
        
        if file_content is None:
            return -1
        else:
            return GitUtils.get_method_end_line(file_content, method_name, start_line)
    
    @staticmethod
    def get_method_end_line(file_content: str, method_name, start_line):
        """
        Get the end line number of a method in a Java file using regex.
        
        Args:
            file_path (str): Path to the Java file.
            method_name (str): Name of the method.
            start_line (int): Starting line number of the method.

        Returns:
            int: End line number of the method. Returns -1 if not found.
        """
        lines = file_content.splitlines()

        # Extract the method body based on curly braces
        brace_count = 0
        inside_method = False

        for i, line in enumerate(lines[start_line:], start=start_line):
            if '{' in line:
                inside_method = True
                brace_count += line.count('{') - line.count('}')
                continue

            if inside_method:
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    return i  # Current line is the end of the method

        return -1

def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []

    # Sort by start value
    ranges.sort(key=lambda r: r[0])
    merged = [ranges[0]]

    for current in ranges[1:]:
        last = merged[-1]
        # Check if current range overlaps or is a subset of the last merged range
        if current[0] <= last[1]:  # Overlapping or touching
            # Merge the two ranges
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)

    return merged