#!/usr/bin/env python3
import os
import sys

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["nnUNet_compile"] = "False"

sys.path.append("/usr/local/lib/python3.10/dist-packages")

from pathlib import Path
from nnunetv2.inference.predict_from_raw_data import predict_entry_point

IMAGES_TS_DIR = Path("/app/imagesTs")
OUTPUT_DIR = Path("/output")
RESULTS_DIR = "/weights"

def main():
    print(">>> Initializing ORION deep learning inference...")

    os.environ["nnUNet_results"] = RESULTS_DIR
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

    args = [
        "-i", str(IMAGES_TS_DIR),
        "-o", str(OUTPUT_DIR),
        "-d", "1",
        "-c", "3d_fullres",
        "-tr", "nnUNetTrainer",
        "-f", "all",
        "-chk", "checkpoint_best.pth",
        "-device", "cpu",
        "-npp", "0",
        "-nps", "0",
        "--save_probabilities"
    ]

    print(f">>> Arguments passed to nnUNet: {args}")

    try:
        sys.argv = ["nnUNet_predict"] + args
        predict_entry_point()
    except Exception as e:
        print(f"!!! Error during inference: {e}")
        exit(1)

    print("\n>>> Applying nomenclature to output segmentations...")
    for file_path in OUTPUT_DIR.iterdir():
        if file_path.is_file() and not file_path.name.startswith("orion_"):
            new_name = "orion_" + file_path.name
            file_path.rename(OUTPUT_DIR / new_name)

    print(">>> ORION pipeline finished successfully!")

if __name__ == "__main__":
    main()
