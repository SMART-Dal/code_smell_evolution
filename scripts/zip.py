import os
import argparse
import zipfile
import config

def zip_dir(dir_path, zip_path):
    """
    Zip a directory.

    :param dir_path: Path to the directory to be zipped.
    :param zip_path: Path to the output zip file.
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                zip_file.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(dir_path, '..')))
                
def unzip_file(zip_path, extract_to):
    """
    Unzip a file.

    :param zip_path: Path to the zip file.
    :param extract_to: Path to the directory where the file will be extracted.
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        zip_file.extractall(extract_to)
    
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
    
    # corpus_generator = prepare_corpus(REPO_IDX, clone=False)
    corpus_generator = [
        ('bitwig', 'bitwig-extensions', os.path.join(config.CORPUS_PATH, 'bitwig', 'bitwig-extensions')),
        ('cgerard321', 'champlain_petclinic', os.path.join(config.CORPUS_PATH, 'cgerard321', 'champlain_petclinic')),
        ('fabricmc', 'mixin', os.path.join(config.CORPUS_PATH, 'fabricmc', 'mixin')),
        ('falsehoodmc', 'fabrication', os.path.join(config.CORPUS_PATH, 'falsehoodmc', 'fabrication')),
        ('linlinjava', 'litemall', os.path.join(config.CORPUS_PATH, 'linlinjava', 'litemall')),
        ('mapbox', 'mapbox-java', os.path.join(config.CORPUS_PATH, 'mapbox', 'mapbox-java')),
        ('marvionkirito', 'altoclef', os.path.join(config.CORPUS_PATH, 'marvionkirito', 'altoclef')),
        ('reneargento', 'algorithms-sedgewick-wayne', os.path.join(config.CORPUS_PATH, 'reneargento', 'algorithms-sedgewick-wayne')),
        ('serg-delft', 'andy', os.path.join(config.CORPUS_PATH, 'serg-delft', 'andy')),
        ('skbkontur', 'extern-java-sdk', os.path.join(config.CORPUS_PATH, 'skbkontur', 'extern-java-sdk')),
        ('sublinks', 'sublinks-api', os.path.join(config.CORPUS_PATH, 'sublinks', 'sublinks-api')),
        ('thombergs', 'code-examples', os.path.join(config.CORPUS_PATH, 'thombergs', 'code-examples')),
        ('warmuuh', 'milkman', os.path.join(config.CORPUS_PATH, 'warmuuh', 'milkman')),
    ]
    (username, repo_name, _)  = corpus_generator[args.idx]
    
    if args.type == "smells":
        target_path = os.path.join(DESIGNITE_OP_DIR, username, repo_name)
    elif args.type == "refs":
        target_path = os.path.join(REFMINER_OP_DIR, username, f"{repo_name}.json")    
    
    if args.action == "zip":
        zip_dir(target_path, os.path.join(zip_lib_path, f'{args.type}_{args.idx}.zip'))
    elif args.action == "unzip":
        unzip_file(os.path.join(zip_lib_path, f'{args.type}_{args.idx}.zip'), target_path)