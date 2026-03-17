import json
import os 

# Get the directory of the currently executing script
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)
print("Current Working Directory:", os.getcwd())

# Path to the input and output JSON files
input_file = "../json/amis_chinese_translations.json"
output_file = "../json/cleaned_amis_chinese_translations.json"

def remove_duplicates(input_file, output_file):
    # Load the data from the JSON file
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Dictionary to store unique translations
    unique_translations = {}
    cleaned_data = []

    for entry in data:
        # Create a tuple of (formosan, chinese) to check for duplicates
        formosan_text = entry["formosan"]
        chinese_text = entry["chinese"]
        key = (formosan_text, chinese_text)

        # Add to dictionary if not already present
        if key not in unique_translations:
            unique_translations[key] = entry
            cleaned_data.append(entry)

    # Save the cleaned data to a new JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

    print(f"Duplicates removed. Total unique translations: {len(cleaned_data)}")

if __name__ == "__main__":
    remove_duplicates(input_file, output_file)
