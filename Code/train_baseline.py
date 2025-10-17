import os
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
from sklearn.metrics import roc_curve, auc
from data_loading.dataset_loader import FeatureDataset
from models.baseline_cnn import LCNNBaseline
from data_loading.streaming_dataset_loader import StreamingFeatureDataset

# ------------------------------------------------------------
# ⚙️ CONFIGURATION
# ------------------------------------------------------------
manifest = r"D:\UNI\FYP\data\features\features_manifest_labeled.csv"
feature_type = "lfcc"       # or "mel"
batch_size, epochs, lr = 64, 6, 1e-3
device = "cuda" if torch.cuda.is_available() else "cpu"
save_path = r"D:\UNI\FYP\models_saved\baseline_cnn.pth"
os.makedirs(os.path.dirname(save_path), exist_ok=True)

# ------------------------------------------------------------
# 📂 LOAD DATA (streaming-safe)
# ------------------------------------------------------------
from data_loading.streaming_dataset_loader import StreamingFeatureDataset

df = pd.read_csv(manifest)
df = df[df["label"].isin(["bonafide", "spoof"])].reset_index(drop=True)

# Stratified 80/20 split
bon = df[df.label == "bonafide"]
spf = df[df.label == "spoof"]
train_df = pd.concat([
    bon.sample(frac=0.8, random_state=42),
    spf.sample(frac=0.8, random_state=42)
])
val_df = df.drop(train_df.index).reset_index(drop=True)
train_df = train_df.reset_index(drop=True)

# --- STREAMING DATALOADERS ---
train_ds = StreamingFeatureDataset(train_df, feature_type=("lfcc" if feature_type == "lfcc" else "mel"), shuffle=True)
val_ds   = StreamingFeatureDataset(val_df,   feature_type=("lfcc" if feature_type == "lfcc" else "mel"), shuffle=False)

train_dl = DataLoader(train_ds, batch_size=batch_size)
val_dl   = DataLoader(val_ds,   batch_size=batch_size)


# ------------------------------------------------------------
# 🧠 MODEL + OPTIMIZER
# ------------------------------------------------------------
model = LCNNBaseline().to(device)
criterion = nn.CrossEntropyLoss()
optimzr = optim.Adam(model.parameters(), lr=lr)

# ------------------------------------------------------------
# 📊 METRIC FUNCTION
# ------------------------------------------------------------
def evaluate(model, loader):
    model.eval()
    all_y, all_s = [], []
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            logits = model(x)
            probs = torch.softmax(logits, dim=1)[:, 1]  # Probability of bonafide
            all_y.append(y.cpu().numpy())
            all_s.append(probs.cpu().numpy())

    y = np.concatenate(all_y)
    s = np.concatenate(all_s)

    fpr, tpr, _ = roc_curve(y, s, pos_label=1)
    fnr = 1 - tpr
    idx = np.nanargmin(np.abs(fnr - fpr))
    eer = (fnr[idx] + fpr[idx]) / 2
    return eer, auc(fpr, tpr)

# ------------------------------------------------------------
# 🚀 TRAINING LOOP
# ------------------------------------------------------------
train_losses, val_eers, val_aucs = [], [], []

print(f"Starting training on {device}...\n")
for ep in range(1, epochs + 1):
    model.train()
    total_loss = 0.0

    for x, y in train_dl:
        x, y = x.to(device), y.to(device)
        optimzr.zero_grad()
        loss = criterion(model(x), y)
        loss.backward()
        optimzr.step()
        total_loss += loss.item()

    # Evaluate each epoch
    avg_loss = total_loss / len(train_dl)
    eer, roc_auc = evaluate(model, val_dl)

    train_losses.append(avg_loss)
    val_eers.append(eer * 100)
    val_aucs.append(roc_auc)

    print(f"Epoch {ep:02d} | Train Loss: {avg_loss:.4f} | Val EER: {eer*100:.2f}% | ROC-AUC: {roc_auc:.3f}")

# ------------------------------------------------------------
# 💾 SAVE MODEL
# ------------------------------------------------------------
torch.save(model.state_dict(), save_path)
print(f"\n✅ Model training complete. Saved to: {save_path}")

# ------------------------------------------------------------
# 📈 PLOT METRICS
# ------------------------------------------------------------
plt.figure(figsize=(10, 5))

# Training Loss
plt.subplot(1, 2, 1)
plt.plot(train_losses, label="Train Loss", marker="o")
plt.title("Training Loss per Epoch")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.grid(True)
plt.legend()

# Validation EER + ROC-AUC
plt.subplot(1, 2, 2)
plt.plot(val_eers, label="Validation EER (%)", marker="o", color="r")
plt.plot(val_aucs, label="Validation ROC-AUC", marker="s", color="g")
plt.title("Validation Performance per Epoch")
plt.xlabel("Epoch")
plt.ylabel("Metric Value")
plt.grid(True)
plt.legend()

plt.tight_layout()
plot_path = r"D:\UNI\FYP\reports\figures\training_curves.png"
os.makedirs(os.path.dirname(plot_path), exist_ok=True)
plt.savefig(plot_path)
plt.show()

print(f"\n📊 Training plots saved to: {plot_path}")
