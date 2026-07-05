#!/usr/bin/env python3
from pathlib import Path
import subprocess
import shutil
import os

INPUT_DIR = Path("/input")
PREDICTIONS_DIR = Path("/output")
TEMP_FINAL_DIR = Path("/app/temp_final_seg")
DRY_RUN = False

def run(cmd):
    cmd_str = [str(x) for x in cmd]
    print(f">>> {' '.join(cmd_str)}")
    if not DRY_RUN:
        subprocess.run(cmd_str, check=True)

def get_original_orientation(img_path: Path):
    result = subprocess.run(["fslhd", str(img_path)], capture_output=True, text=True)
    out = result.stdout
    
    def parse_orient(header_text, form_type="sform"):
        codes = []
        for axis in ['x', 'y', 'z']:
            for line in header_text.split('\n'):
                if line.startswith(f'{form_type}_{axis}orient'):
                    val = line.split()[1]
                    if val == "Unknown":
                        return None
                    parts = val.split('-to-')
                    codes.append(parts[0][0] + parts[1][0])
        return codes if len(codes) == 3 else None

    orientation = parse_orient(out, "sform")
    if not orientation:
        orientation = parse_orient(out, "qform")
        
    return orientation

def main():
    if TEMP_FINAL_DIR.exists():
        shutil.rmtree(TEMP_FINAL_DIR)
    TEMP_FINAL_DIR.mkdir(parents=True, exist_ok=True)

    mask_files = sorted(list(PREDICTIONS_DIR.glob("*.nii.gz")))
    print(f"--- Found {len(mask_files)} nnU-Net segmentations to revert ---")

    for mask_path in mask_files:
        base_name = mask_path.name
        print(f"\n>>> Processing segmentation: {base_name}")
        
        original_name = base_name.replace("orion_", "")
        orig_img_path = INPUT_DIR / original_name
        
        if not orig_img_path.exists():
            print(f" [WARNING] Original RAW image not found for: {original_name}")
            continue
            
        orig_ori = get_original_orientation(orig_img_path)
        
        if not orig_ori:
            print(f" [ERROR] Could not read original axes for: {original_name}")
            continue
            
        print(f"    Original axes detected: {orig_ori[0]} {orig_ori[1]} {orig_ori[2]}")
        
        temp_out_mask = TEMP_FINAL_DIR / original_name
        
        run([
            "fslswapdim",
            mask_path,
            orig_ori[0], orig_ori[1], orig_ori[2],
            temp_out_mask
        ])
        
        run(["fslcpgeom", orig_img_path, temp_out_mask, "-d"])
        
        print(f" [OK] Mask aligned: {original_name}")

    print("\n>>> Cleaning up raw predictions and saving final outputs...")
    
    for item in PREDICTIONS_DIR.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)

    for final_mask in TEMP_FINAL_DIR.glob("*.nii.gz"):
        shutil.move(str(final_mask), str(PREDICTIONS_DIR / final_mask.name))

    shutil.rmtree(TEMP_FINAL_DIR)

    print("\n=== FINISHED ===")
    print(f"All final segmentations are exclusively saved in: {PREDICTIONS_DIR}")

if __name__ == "__main__":
    main()
