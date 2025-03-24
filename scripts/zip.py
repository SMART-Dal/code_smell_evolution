import os
import argparse
import zipfile
import config
from corpus import prepare_repo

def zip_dir(dir_path, zip_path):
    """
    Zip a directory.

    :param dir_path: Path to the directory to be zipped.
    :param zip_path: Path to the output zip file.
    """
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.isdir(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, dir_path)
                        zipf.write(file_path, arcname)
            else:
                zipf.write(dir_path, os.path.basename(dir_path))
        print(f"Successfully compressed '{dir_path}'.")
    except Exception as e:
        print(f"Error while zipping '{dir_path}': {e}")
def unzip_file(zip_path, extract_to):
    """
    Unzip a file.

    :param zip_path: Path to the zip file.
    :param extract_to: Path to the directory where the file will be extracted.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            zip_file.extractall(extract_to)
        print(f"Successfully extracted '{zip_path}' to '{extract_to}'.")
    except Exception as e:
        print(f"Error while extracting '{zip_path}': {e}")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="zip/unzip a directory.")
    parser.add_argument("action", type=str, choices=["zip", "unzip"], help="action to perform.")
    parser.add_argument("type", type=str, choices=["smells", "refs"], help="type of the directory to process.")
    parser.add_argument("idx", type=int, help="index of the repository to process.")
    args = parser.parse_args()
    
    zip_lib_path = os.path.join(config.OUTPUT_PATH, "zips")
    if not os.path.exists(zip_lib_path):
        os.makedirs(zip_lib_path)
        
    DESIGNITE_OP_DIR = os.path.join(config.OUTPUT_PATH, 'Designite_OP')
    REFMINER_OP_DIR = os.path.join(config.OUTPUT_PATH, 'RefMiner_OP')
    
    (username, repo_name, _) = prepare_repo(args.idx, clone=False)
    
    if args.action == "unzip":
        P = os.path.join(DESIGNITE_OP_DIR, username, repo_name) if args.type == "smells" else os.path.join(REFMINER_OP_DIR, username)
        if not os.path.exists(P):
            os.makedirs(P)
    
    
    if args.type == "smells":
        target_dir = os.path.join(DESIGNITE_OP_DIR, username, repo_name)
    elif args.type == "refs":
        target_dir = os.path.join(REFMINER_OP_DIR, username)
        
    # Validate target path
    if not os.path.exists(target_dir):
        print(f"Error: Target path '{target_dir}' does not exist.")
        exit(1)
    
    if args.action == "zip":
        zip_dir(target_dir, os.path.join(zip_lib_path, f'{args.type}_{args.idx}.zip'))
    elif args.action == "unzip":
        unzip_file(os.path.join(zip_lib_path, f'{args.type}_{args.idx}.zip'), target_dir)