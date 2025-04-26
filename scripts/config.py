import os

CURR_DIR = os.path.dirname(os.path.realpath(__file__))

if CURR_DIR.endswith("scripts"):
    ROOT_PATH = os.path.dirname(CURR_DIR)
else:
    ROOT_PATH = ".."

BIN_PATH = os.path.join(ROOT_PATH, "bin")
EXECUTABLES_PATH = os.path.join(BIN_PATH, "executables")
REPO_LIST_PATH = os.path.join(BIN_PATH, "data", "results.json")
CORPUS_SPECS_PATH  = os.path.join(BIN_PATH, "data", "corpus_spec.json")

REPOS_PATH = os.path.join(ROOT_PATH, "repos")
CORPUS_PATH = os.path.join(ROOT_PATH, "corpus")
OUTPUT_PATH = os.path.join(ROOT_PATH, "output")
ZIP_LIB = os.path.join(OUTPUT_PATH, "zips")
PLOTS_PATH = os.path.join(OUTPUT_PATH, "plots")
MANUAL_ANALYSIS_PATH = os.path.join(OUTPUT_PATH, "manual_analysis")
MANUAL_ANALYSIS_FOR_UNMAPPED_PATH = os.path.join(OUTPUT_PATH, "manual_analysis_for_unmapped")

SMELL_REF_MAP_PATH = os.path.join(OUTPUT_PATH, "smell_ref_map")

SMELL_SKIP_COLS = ["Project Name"]

class OpenAI:
    MODEL = "gpt-4o-mini"
    ENDPOINT = "https://api.openai.com/v1/chat/completions"
    API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    HEADERS = {
        "Authorization" : f"Bearer {API_KEY}",
        "Content-Type" : "application/json"
    }
    TPM = 200000
    RPM = 500