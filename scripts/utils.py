import os

def get_repo_name(repo_path):
    """
    Get the name of the repository folder.

    :param repo_path: Path to the local Git repository.
    :return: The name of the repository folder.
    """
    return os.path.basename(os.path.normpath(repo_path))

def get_git_branches(repo_path):
    """
    Get a list of branches in a Git repository.

    :param repo_path: Path to the local Git repository.
    :return: A list of branch names.
    """
    branches = []
    try:
        # Run git branch command and capture the output
        output = os.popen(f'cd {repo_path} && git branch').read()
        # Process the output to get branch names
        branches = [line.strip().lstrip('* ') for line in output.split('\n') if line]
    except Exception as e:
        print(f"An error occurred: {e}")
    return branches