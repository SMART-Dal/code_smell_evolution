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

REPOS_PATH = os.path.join(ROOT_PATH, "repos")
OUTPUT_PATH = os.path.join(ROOT_PATH, "output")

class SmellCols(Enum):
    arch_smells_inst = ["Project Name", "Package Name", "Architecture Smell"]
    design_smells_inst = ["Project Name", "Package Name", "Type Name", "Design Smell"]
    impl_smells_inst = ["Project Name", "Package Name", "Type Name", "Method Name", "Implementation Smell", "Method start line no"]
    testability_smells_inst = ["Project Name", "Package Name", "Type Name", "Testability Smell"]
    test_smells_inst = ["Project Name", "Package Name", "Type Name", "Method Name", "Test Smell"]