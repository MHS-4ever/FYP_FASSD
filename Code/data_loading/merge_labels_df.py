import os
import pandas as pd

# --- paths
features_manifest = r"D:\UNI\FYP\data\features\features_manifest.csv"
metadata_file = r"D:\UNI\FYP\DataSet\English\keys\DF\CM\trial_metadata.txt"
out_csv = r"D:\UNI\FYP\data\features\features_manifest_labeled.csv"

# --- load features manifest
feat = pd.read_csv(features_manifest)

# --- read metadata and extract needed columns
cols = ["system_id", "filename", "codec", "protocol", "attack_id", "label"]
meta = pd.read_csv(metadata_file, sep=r"\s+", header=None, usecols=[0,1,2,3,4,5], names=cols)

# normalize filenames
meta["filename"] = meta["filename"].astype(str) + ".wav"
meta = meta[["filename", "label"]]

# --- merge
merged = feat.merge(meta, on="filename", how="left", suffixes=("", "_meta"))

# If a 'label_meta' column exists (true labels), replace the old placeholder
if "label_meta" in merged.columns:
    merged.drop(columns=["label"], inplace=True, errors="ignore")
    merged.rename(columns={"label_meta": "label"}, inplace=True)

# Fill any missing labels
missing = merged["label"].isna().sum()
if missing > 0:
    print(f"⚠️ Warning: {missing} files not found in metadata. Marked as 'unknown'.")
    merged["label"] = merged["label"].fillna("unknown")

# Show distribution
print("Label distribution:\n", merged["label"].value_counts(dropna=False))

# --- save
merged.to_csv(out_csv, index=False)
print(f"\n✅ Labeled manifest saved to: {out_csv}")


# fill missing
missing = merged["label"].isna().sum()
if missing > 0:
    print(f"⚠️ Warning: {missing} files not found in metadata. Marked as 'unknown'.")
    merged["label"] = merged["label"].fillna("unknown")

# check label distribution
print("Label distribution:\n", merged["label"].value_counts(dropna=False))

# --- save
merged.to_csv(out_csv, index=False)
print(f"\n✅ Labeled manifest saved to: {out_csv}")
