from sklearn.metrics import cohen_kappa_score
from utils import FileUtils
import config

def funct1():
    target_dir = config.MANUAL_ANALYSIS_PATH
    for f in FileUtils.traverse_directory(target_dir):
        f_data = FileUtils.load_json_file(f)
        
        for d in f_data:
            try:
                d["human_analysis"]["correct_mapping?"] = d["llm_analysis"]["correct_mapping?"]
                d["human_analysis"]["decreases_severity?"] = d["llm_analysis"]["decreases_severity?"]
            except Exception as e:
                print(f"An error occurred: {e}")
        
        # Save the updated data back to the JSON file
        FileUtils.save_json_file(f, f_data)
        print(f"Updated {f} with human analysis data.")
        
def calculate_kappa():
    human_res = []
    llm_res = []
    
    target_dir = config.MANUAL_ANALYSIS_PATH
    for f in FileUtils.traverse_directory(target_dir):        
        f_data = FileUtils.load_json_file(f)
        
        for d in f_data:
            try:
                human_res.append(d["human_analysis"]["correct_mapping?"])
                llm_res.append(d["llm_analysis"]["correct_mapping?"])
            except Exception as e:
                print(f"An error occurred: {e}")
        
    # Calculate Cohen's Kappa score
    kappa_score = cohen_kappa_score(human_res, llm_res)
    print(f"Cohen's Kappa Score: {kappa_score}")

if __name__ == "__main__":
    calculate_kappa()