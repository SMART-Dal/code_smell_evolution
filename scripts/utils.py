import os
import json
import csv
import subprocess
import traceback
from git import Repo
from tree_sitter import Language, Parser, Tree, Node, Query
import tree_sitter_java as tsjava

def log_execution(func):
    def wrapper(*args, **kwargs):
        # Determine class name if the function is a method
        class_name = None
        if args:
            class_name = args[0].__class__.__name__ if hasattr(args[0], "__class__") else None

        # Log the custom message and function execution details
        if class_name:
            print(f"▶ Starting execution of {class_name}.{func.__name__}")
        else:
            print(f"▶ Starting execution of {func.__name__}")

        try:
            result = func(*args, **kwargs)
            if class_name:
                print(f"✔ Finished execution of {class_name}.{func.__name__}")
            else:
                print(f"✔ Finished execution of {func.__name__}")
            return result
        except Exception as e:
            if class_name:
                print(f"✖ Error occurred in {class_name}.{func.__name__}: {e}")
            else:
                print(f"✖ Error occurred in {func.__name__}: {e}")
                
            # Log the full error traceback
            traceback_str = traceback.format_exc()
            print(f"Traceback: {traceback_str}")
            raise
    return wrapper



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
    
    @staticmethod
    def checkout_repo(repo_path, commit_hash) -> bool:
        try:
            subprocess.run("git", "checkout", commit_hash, cwd=repo_path)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error git checkout for repo - {repo_path}, commit - {commit_hash}: Error: {e.stderr}")
            return False
    
class TSManager:
    def __init__(self) -> None:
        JAVA_LANG = tsjava.language()
        self.language = Language(JAVA_LANG)
        self.parser = Parser(JAVA_LANG)
        
    def _generate_tree(self, file_path) -> Tree:
        """
        Generate the Tree-sitter tree for a given file.
        
        :param file_path: Path to the file to parse
        :return: A Tree-sitter Tree object
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                source_code = file.read()
            
            tree = self.parser.parse(bytes(source_code, "utf8"))
            return tree
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Error generating tree: {e}")
    
    def get_functions_data(self, file_path: str):
        """
        Extract all function names and their ranges from a Java file using Tree-Sitter queries.
        
        :param file_path: Path to the Java file
        :return: A list of tuples, each containing a function name and its range as (start_line, start_col, end_line, end_col)
        """
        query_str = """
        (method_declaration) @function_def
        """
        tree = self._generate_tree(file_path)
        # source_code = open(file_path, 'r', encoding='utf-8').read()
        # root_node = tree.root_node
        
        query = Query(self.language, query_str)
        # cursor = ts.TreeCursor
        captures = query.captures(tree.root_node)
        # matches = cursor.exec_query(query, root_node, bytes(source_code, "utf8"))
        
        functions = []
        for capture in captures:
            for (capture_node, capture_name) in capture:
                capture_node: Node
                if capture_name == "function_def":
                    func_name = self._get_function_node_name(capture_node)
                    start_point = (capture_node.start_point.row, capture_node.start_point.column)
                    end_point = (capture_node.end_point.row, capture_node.end_point.column)
                    functions.append((func_name, start_point, end_point))
        return functions
    
    def _get_function_node_name(self, n: Node) -> str:
        res = n.child_by_field_name("name")
        if res:
            return res.text.decode()
        else:
            return None