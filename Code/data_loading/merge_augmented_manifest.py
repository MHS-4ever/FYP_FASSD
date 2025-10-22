import pandas as pd
import os

clean_manifest = r"E:\FYP\data\features\features_manifest_labeled.csv"
aug_manifest   = r"E:\FYP\data\features_augmented\augmentation_checkpoint.csv"
output_path    = r"E:\FYP\data\features_merged\features_manifest_combined.csv"

os.makedirs(os.path.dirname(output_path), exist_ok=True)

df_clean = pd.read_csv(clean_manifest)
df_aug   = pd.read_csv(aug_manifest)

# Mark dataset type for reference (optional)
df_clean['source'] = 'clean'
df_aug['source']   = 'augmented'

df_combined = pd.concat([df_clean, df_aug], ignore_index=True)
df_combined.to_csv(output_path, index=False)

print(f"✅ Combined manifest saved: {output_path}")
print(f"Total samples: {len(df_combined)} (Clean: {len(df_clean)}, Aug: {len(df_aug)})")
