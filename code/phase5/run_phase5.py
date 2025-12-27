"""
Phase 5 runner: evaluate the trained hybrid model on the speaker-independent test set.

This is a thin wrapper around evaluate_hybrid_model.py with sensible defaults.
"""

import os
import sys
import subprocess


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    ckpt = os.path.join(repo_root, "models_saved", "hybrid_resnet_environmental_best.pth")
    test_manifest = os.path.join(repo_root, "data", "manifests", "test_speaker_independent.csv")
    train_manifest = os.path.join(repo_root, "data", "manifests", "train_speaker_independent.csv")

    # Defaults match the proven PC setup.
    spectrogram_h5 = "C:/FYP/data/features/logmel_chunked.h5"
    environmental_h5 = "C:/FYP/data/features/environmental_packed.h5"
    output_dir = os.path.join(repo_root, "reports", "evaluation")

    cmd = [
        sys.executable,
        os.path.join(repo_root, "code", "phase5", "evaluate_hybrid_model.py"),
        "--ckpt", ckpt,
        "--test_manifest", test_manifest,
        "--train_manifest", train_manifest,
        "--spectrogram_h5", spectrogram_h5,
        "--environmental_h5", environmental_h5,
        "--output_dir", output_dir,
        "--batch_size", "256",
    ]

    print("[PHASE5] Running:")
    print(" ".join(cmd))
    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()


