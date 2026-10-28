import os
import re
import glob
import pandas as pd

# 1. Set the folder path containing all your raw CSV files
folder_path = r"C:\Users\hs916\Desktop\PLL hs916\data\6.6\PC2\RCvary-alt"

# Find all CSV files in that folder
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

print(f"Found {len(csv_files)} CSV files. Starting conversion...\n")

for filename in csv_files:
    # Skip files that have already been reformatted
    if "_reformatted" in filename:
        continue

    print(f"Processing: {os.path.basename(filename)}")
    
    try:
        # Read the raw CSV
        df = pd.read_csv(filename)
        
        # 2. DYNAMIC HEADERS: Pull exact headers from the file
        # This ignores the extra "Unnamed" columns Pandas creates from trailing commas
        headers = [str(col).strip() for col in df.columns if 'Unnamed' not in str(col)]
        
        if len(df) < len(headers):
            print("  -> Skipped: File does not seem to match the expected nasty format.")
            continue

        raw_strings = df.iloc[:, 0].astype(str).tolist()
        
        clean_data = {}
        time_col_name = None
        time_start = 0.0
        time_step = 1.0e-6 # Default fallback just in case

        # 3. Parse each row based dynamically on the headers it found
        for i, col_name in enumerate(headers):
            if i >= len(raw_strings):
                break
                
            sanitized_text = raw_strings[i].replace('np.float64', '')
            
            # Extract actual numbers and 'nan'
            matches = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?|nan", sanitized_text, flags=re.IGNORECASE)
            
            # 4. DYNAMIC TIME: Check if this column is the "time" column
            if 'time' in col_name.lower():
                time_col_name = col_name
                # Pull the start time and the exact time step automatically from the first two numbers
                if len(matches) >= 2:
                    time_start = float(matches[0])
                    time_step = float(matches[1]) - float(matches[0])
                    print(f"     [+] Detected time start: {time_start}, step: {time_step}")
            else:
                # Store standard data
                clean_data[col_name] = [float(x) for x in matches]

        # Failsafe if it found no valid data
        if not clean_data:
            print("  -> Skipped: Could not extract any valid column data.")
            continue

        # Trim all lists to the shortest length so they match perfectly without errors
        min_length = min(len(lst) for lst in clean_data.values())
        for key in clean_data:
            clean_data[key] = clean_data[key][:min_length]
            
        # 5. Recreate the time list dynamically using the detected step
        if time_col_name:
            clean_data[time_col_name] = [time_start + (j * time_step) for j in range(min_length)]
            
        # 6. Reorder the dictionary so it matches the exact original header layout
        ordered_data = {col: clean_data[col] for col in headers if col in clean_data}

        # Dynamically create the new filename
        base_name = os.path.basename(filename)
        name_without_ext, extension = os.path.splitext(base_name)
        output_filename = os.path.join(folder_path, f"{name_without_ext}{extension}")

        # Convert to a standard Pandas DataFrame and save
        clean_df = pd.DataFrame(ordered_data)
        
        # na_rep='0' forces any missing (NaN) values to explicitly print as 0 in the CSV
        clean_df.to_csv(output_filename, index=False, na_rep='0')

        print(f"  -> Success: Saved {min_length} rows to {os.path.basename(output_filename)}")

    except Exception as e:
        print(f"  -> Error processing file: {e}")

print("\nAll files processed successfully!")