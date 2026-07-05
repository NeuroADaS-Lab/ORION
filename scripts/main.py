#!/usr/bin/env python3
import subprocess
import sys

def main():
    print("==========================================")
    print("       ORION CLINICAL PIPELINE v1.0       ")
    print("==========================================")

    try:
        print("\n[PHASE 1] Preprocessing & Spatial Bounding Box...")
        subprocess.run(["python3", "/app/scripts/preprocess.py"], check=True)

        print("\n[PHASE 2] nnU-Net Inference...")
        subprocess.run(["python3", "/app/scripts/predict.py"], check=True)

        print("\n[PHASE 3] Postprocessing & Geometry Restoration...")
        subprocess.run(["python3", "/app/scripts/postprocess.py"], check=True)

        print("\n==========================================")
        print("  PIPELINE COMPLETED SUCCESSFULLY!        ")
        print("  Check your mapped /output directory.    ")
        print("==========================================")
    
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Pipeline failed during execution. Exit code: {e.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    main()
