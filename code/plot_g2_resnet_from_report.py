"""Plot G.2 ResNet CM from documented Phase 4.2 augmented-test results."""
import os
import matplotlib.pyplot as plt
import numpy as np

# Source: reports/previous_phases/PHASE4_2_RESULTS.md (augmented test confusion matrix)
cm = np.array([[21853, 764], [13620, 575592]], dtype=int)
out_dir = os.path.join("submissions", "thesis_preparation", "figures", "appendix_g")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "G2_resnet_confusion_matrix.png")

fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
fig.colorbar(im, ax=ax)
ax.set_title("ResNet CNN — Augmented Test (n=611,829)\nEER=2.61%, AUC=0.997", fontsize=12, fontweight="bold")
ax.set_xlabel("Predicted label")
ax.set_ylabel("True label")
labels = ["Bonafide", "Spoof"]
ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(labels)
ax.set_yticklabels(labels)
thresh = cm.max() * 0.5
for i in range(2):
    for j in range(2):
        ax.text(j, i, f"{cm[i,j]:,}", ha="center", va="center",
                color="white" if cm[i,j] > thresh else "black", fontsize=10)
fig.tight_layout()
fig.savefig(out_path, dpi=200, bbox_inches="tight")
plt.close()
print(f"[SAVE] {out_path}")
