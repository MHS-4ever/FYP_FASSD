"""
Convenience runner for Phase 6 explanation on raw audio.
Defaults to the laptop paths and testing_audios folder.
"""

import os
import sys
import subprocess


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ckpt = os.path.join(repo_root, "models_saved", "hybrid_resnet_environmental_best.pth")

    # Prefer the workspace-local `testing_audios/` folder when available.
    audio_dir = os.path.join(repo_root, "testing_audios")
    output_dir = os.path.join(repo_root, "reports", "explanation_examples")

    cmd = [
        sys.executable,
        os.path.join(repo_root, "code", "phase6", "explain_prediction.py"),
        "--ckpt", ckpt,
        "--audio_dir", audio_dir,
        "--output_dir", output_dir,
        "--batch_size", "32",
        "--threshold", "0.5",
    ]

    print("[PHASE6] Running:")
    print(" ".join(cmd))
    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()


