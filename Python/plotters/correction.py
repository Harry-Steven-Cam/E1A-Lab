import os
import re
import glob
import pandas as pd

# 1. Set the folder path containing all your raw CSV files
folder_path = r"C:\Users\hs916\Desktop\PLL hs916\data\6.6\PC1\Noise-alt"

# Find all CSV files in that folder
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

# Define the variables based on the row order in your files
var_names = ['time', 'awg_freq', 'vco_freq', 'ratio', 'phase_diff', 'vco_in_val']
time_step = 1.0e-6 

print(f"Found {len(csv_files)} CSV files. Starting conversion...\n")

for filename in csv_files:
    # Skip files that have already been reformatted
    if "_reformatted" in filename:
        continue

    print(f"Processing: {os.path.basename(filename)}")
    
    try:
        # Read the raw CSV
        df = pd.read_csv(filename)
        
        # Check if it actually contains the trapped 'nasty' format strings
        if len(df) < 6:
            print("  -> Skipped: File does not match the 6-row raw format.")
            continue

        # Grab all the messy strings trapped in the first column
        raw_strings = df.iloc[:, 0].astype(str).tolist()
        clean_data = {}

        # Parse rows 1 through 5 into python lists
        for i in range(1, 6):
            # Remove 'np.float64' before extracting numbers
            sanitized_text = raw_strings[i].replace('np.float64', '')
            
            # Extract actual numbers and 'nan'
            matches = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?|nan", sanitized_text, flags=re.IGNORECASE)
            clean_data[var_names[i]] = [float(x) for x in matches]

        # Trim all lists to the shortest length so they match perfectly
        min_length = min(len(lst) for lst in clean_data.values())
        for key in clean_data:
            clean_data[key] = clean_data[key][:min_length]
            
        # Recreate the time list dynamically 
        clean_data['time'] = [i * time_step for i in range(min_length)]

        # Dynamically create the new filename
        base_name = os.path.basename(filename)
        name_without_ext, extension = os.path.splitext(base_name)
        output_filename = os.path.join(folder_path, f"{name_without_ext}_reformatted{extension}")

        # Convert to a standard Pandas DataFrame and save
        clean_df = pd.DataFrame(clean_data)
        clean_df.to_csv(output_filename, index=False)

        print(f"  -> Success: Saved {min_length} rows to {os.path.basename(output_filename)}")

    except Exception as e:
        print(f"  -> Error processing file: {e}")

print("\nAll files processed successfully!")