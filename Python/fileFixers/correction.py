import os
import re
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set the folder path containing your CSV files
folder_path = r"C:\Users\hs916\Desktop\PLL hs916\data\6.6\PC2\Noise"

# Find all CSV files in that folder
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

def plot_vco(time_vals, vco_vals, file_title):
    plt.figure(figsize=(10, 5))
    plt.plot(time_vals, vco_vals, label='VCO Input Voltage', color='blue', linewidth=2)
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('VCO In Val (V)', fontsize=12)
    plt.title(f"VCO Input Voltage vs. Time\n{file_title}", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    print("\n[+] Close the plot window to choose an action...")
    plt.show(block=True) # Pauses script until you close the graph window

print(f"Found {len(csv_files)} files to process.\n")

for filename in csv_files:
    base_name = os.path.basename(filename)
    print("=" * 60)
    print(f"File: {base_name}")
    
    df = pd.read_csv(filename)
    
    # ---------------------------------------------------------------------
    # CASE 1: Standard Clean/Reformatted Format (Normal Columns)
    # ---------------------------------------------------------------------
    if 'vco_in_val' in df.columns and 'time' in df.columns:
        time_vals = df['time'].values
        vco_in_val = df['vco_in_val'].values
        
        # Display the original plot
        plot_vco(time_vals, vco_in_val, f"ORIGINAL: {base_name}")
        
        user_choice = input("Multiply vco_in_val by 10 and save back? (y/n): ").strip().lower()
        
        if user_choice in ['y', 'yes']:
            # Multiply by 10 and update dataframe
            df['vco_in_val'] = df['vco_in_val'] * 10
            df.to_csv(filename, index=False)
            print("  --> Success! Updated clean CSV file.")
            
            # Show updated plot
            plot_vco(df['time'].values, df['vco_in_val'].values, f"MODIFIED (x10): {base_name}")
        else:
            print("  --> Skipped. Moving to next file...")

    # ---------------------------------------------------------------------
    # CASE 2: Old "Nasty" Format (Arrays Trapped in Row Strings)
    # ---------------------------------------------------------------------
    elif len(df) >= 6:
        raw_strings = df.iloc[:, 0].astype(str).tolist()
        
        # Extract vco_in_val numbers (Row index 5)
        vco_text = raw_strings[5].replace('np.float64', '')
        vco_matches = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?|nan", vco_text, flags=re.IGNORECASE)
        vco_in_val = [float(x) for x in vco_matches]
        
        # Extract time parameters dynamically (Row index 0)
        time_text = raw_strings[0].replace('np.float64', '')
        time_matches = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", time_text)
        
        time_start = float(time_matches[0]) if len(time_matches) >= 1 else 0.0
        time_step = (float(time_matches[1]) - time_start) if len(time_matches) >= 2 else 1.0e-6
        
        time_vals = [time_start + (i * time_step) for i in range(len(vco_in_val))]
        
        # Display the original plot
        plot_vco(time_vals, vco_in_val, f"ORIGINAL (Nasty Format): {base_name}")
        
        user_choice = input("Multiply vco_in_val by 10 and save back? (y/n): ").strip().lower()
        
        if user_choice in ['y', 'yes']:
            # Multiply by 10
            new_vco_in_val = [v * 10 for v in vco_in_val]
            
            # Re-encode back into "[np.float64(x), np.float64(y), ...]"
            nasty_items = []
            for v in new_vco_in_val:
                if np.isnan(v):
                    nasty_items.append("nan")
                else:
                    nasty_items.append(f"np.float64({v})")
            
            # Re-inject back into the exact row position
            df.iat[5, 0] = "[" + ", ".join(nasty_items) + "]"
            df.to_csv(filename, index=False)
            print("  --> Success! Preserved nasty format and updated file.")
            
            # Show updated plot
            plot_vco(time_vals, new_vco_in_val, f"MODIFIED x10 (Nasty Format): {base_name}")
        else:
            print("  --> Skipped. Moving to next file...")
    else:
        print("  --> Skipped: Unrecognized file structure.")

print("\n" + "=" * 60)
print("Finished checking all files!")