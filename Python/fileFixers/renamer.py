import os

folder = r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/data"

dry_run = False

files_checked = 0
renamed_count = 0

for root, dirs, files in os.walk(folder):

    for filename in files:

        files_checked += 1

        if "9.9" in filename:

            new_filename = filename.replace("9.9", "10")

            old_path = os.path.join(root, filename)
            new_path = os.path.join(root, new_filename)

            if os.path.exists(new_path):
                print(f"SKIPPED: {old_path}")
                continue

            print(f"Renaming: {filename}")
            print(f"To:       {new_filename}")

            if not dry_run:
                os.rename(old_path, new_path)

            renamed_count += 1

print("\n==============================")
print(f"Files checked: {files_checked}")
print(f"Files renamed: {renamed_count}")
print("==============================")