import os
import json
import config

def merge_json_files(source_path, output_file, prefix):
    try:
        merged_data = {}
        files = os.listdir(source_path)
        json_files = [
            f for f in files 
            if f.endswith('.json') and f.startswith(prefix) and os.path.isfile(os.path.join(source_path, f))
        ]
        for file in json_files:
            file_path = os.path.join(source_path, file)
            with open(file_path, 'r') as f:
                data = json.load(f)
                merged_data.update(data)
                os.remove(file_path)  # Delete the file after merging
        with open(output_file, 'w') as f:
            json.dump(merged_data, f, indent=2)
        print(f"Merged data written to {output_file}")
    except Exception as e:
        print(f"Error while merging JSON files: {e}")

def merge_txt_files(source_path, output_file, prefix):
    try:
        merged_rows = []
        files = os.listdir(source_path)
        txt_files = [
            f for f in files 
            if f.endswith('.txt') and f.startswith(prefix) and os.path.isfile(os.path.join(source_path, f))
        ]
        
        header_added = False  # To track if the header has already been added

        for file in txt_files:
            file_path = os.path.join(source_path, file)
            with open(file_path, 'r') as f:
                rows = f.readlines()
                if rows:
                    header = rows[0].strip()  # First line as header
                    data_rows = [row.strip() for row in rows[1:] if row.strip()]  # Remaining lines as data
                    
                    if not header_added:  # Add the header only once
                        merged_rows.append(header)
                        header_added = True
                    
                    merged_rows.extend(data_rows)
            os.remove(file_path)  # Delete the file after merging

        with open(output_file, 'w') as f:
            f.write("\n".join(merged_rows))
        print(f"Merged rows written to {output_file}")
    except Exception as e:
        print(f"Error while merging TXT files: {e}")

if __name__ == "__main__":
    # purge corpus_info
    merge_json_files(config.CORPUS_PATH, os.path.join(config.CORPUS_PATH, "corpus_info.json"), "corpus_info_")
        
    # purge designite_status
    DESIGNITE_OP_PATH = os.path.join(config.OUTPUT_PATH, "Designite_OP")
    merge_txt_files(DESIGNITE_OP_PATH, os.path.join(DESIGNITE_OP_PATH, "designite_status.txt"), "designite_status_")
    
    # purge refminer_status
    REFMINER_OP_PATH = os.path.join(config.OUTPUT_PATH, "RefMiner_OP")
    merge_txt_files(REFMINER_OP_PATH, os.path.join(REFMINER_OP_PATH, "refminer_status.txt"), "refminer_status_")