import os
from enum import Enum

CURR_DIR = os.path.dirname(os.path.realpath(__file__))

if CURR_DIR.endswith("scripts"):
    ROOT_PATH = os.path.dirname(CURR_DIR)
else:
    ROOT_PATH = ".."

BIN_PATH = os.path.join(ROOT_PATH, "bin")
EXECUTABLES_PATH = os.path.join(BIN_PATH, "executables")
REPO_LIST_PATH = os.path.join(BIN_PATH, "data", "results.json")
CORPUS_SPECS_PATH  = os.path.join(BIN_PATH, "data", "corpus_specs.json")

REPOS_PATH = os.path.join(ROOT_PATH, "repos")
CORPUS_PATH = os.path.join(ROOT_PATH, "corpus")
OUTPUT_PATH = os.path.join(ROOT_PATH, "output")

SMELLS_LIB_PATH = os.path.join(OUTPUT_PATH, "Smells_lifespan_OP")

SMELL_SKIP_COLS = ["Project Name"]
SMELL_COL_NAMES = ["Architecture Smell", "Design Smell", "Implementation Smell", "Testability Smell", "Test Smell"]