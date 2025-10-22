import os
import pandas as pd

# ✅ Use raw strings (r"") to avoid escape errors
manifest_files = [
    r"E:\FYP\data\features\features_manifest_labeled.csv",
    r"E:\FYP\data\features\features_manifest.csv",
    r"E:\FYP\data\features_augmented\augmentation_checkpoint.csv",
    r"E:\FYP\data\manifests\asvspoof2021_df_manifest.csv",
    r"E:\FYP\data\manifests\missing_files.csv",
]

# ✅ Old and new roots as raw strings
old_root = r"D:\\UNI\\FYP"
new_root = r"E:\\FYP"

for path in manifest_files:
    if os.path.exists(path):
        try:
            print(f"🔧 Updating paths in: {path}")
            df = pd.read_csv(path)
            df = df.replace(old_root, new_root, regex=True)
            df.to_csv(path, index=False)
            print(f"✅ Updated successfully: {path}")
        except Exception as e:
            print(f"⚠️ Skipped {path} due to error: {e}")
    else:
        print(f"❌ File not found: {path}")

print("\n🎉 All manifests processed. Drive letter migration completed successfully.")
