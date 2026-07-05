#!/usr/bin/env python3
from pathlib import Path
import subprocess
import shutil
import sys
import numpy as np
import nibabel as nib

def save_volume_as_nifti(volume, affine, header, filename):
    if header is not None:
        new_volume = nib.Nifti1Image(volume, affine, header=header)
    else:
        new_volume = nib.Nifti1Image(volume, affine)
    new_volume.header.set_data_dtype(volume.dtype)
    new_volume.header.set_qform(affine)
    new_volume.header.set_sform(affine)
    nib.save(new_volume, filename)

INPUT_DIR = Path("/input")
IMAGES_TS_DIR = Path("/app/imagesTs")
TEMP_DIR = Path("/app/temp_calc")
REF_IMAGE = Path("/app/resources/orion_reference_template.nii.gz")

MODALITIES = ["T1", "T2", "FLAIR"]
DRY_RUN = False

def run(cmd):
    cmd_str = [str(x) for x in cmd]
    print(f">>> {' '.join(cmd_str)}")
    if not DRY_RUN:
        subprocess.run(cmd_str, check=True)

def get_name(p: Path) -> str:
    return p.name.replace(".nii.gz", "").replace(".nii", "")

if IMAGES_TS_DIR.exists(): shutil.rmtree(IMAGES_TS_DIR)
if TEMP_DIR.exists(): shutil.rmtree(TEMP_DIR)
IMAGES_TS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

ref_std = TEMP_DIR / "ref_std.nii.gz"
run(["fslreorient2std", REF_IMAGE, ref_std])

ref_cropped = TEMP_DIR / "ref_cropped.nii.gz"
run(["robustfov", "-i", ref_std, "-r", ref_cropped])

ref_brain = TEMP_DIR / "ref_brain.nii.gz"
run(["bet", ref_cropped, ref_brain, "-R", "-f", "0.5"])

ref_bin = TEMP_DIR / "ref_bin.nii.gz"
run(["fslmaths", ref_brain, "-bin", ref_bin])

ref_dil = TEMP_DIR / "ref_dil.nii.gz"
run([
    "fslmaths", ref_bin,
    "-dilM", "-dilM", "-dilM", "-dilM", "-dilM",
    "-dilM", "-dilM", "-dilM", "-dilM", "-dilM",
    "-dilM", "-dilM", "-dilM", "-dilM", "-dilM",
    "-dilM", "-dilM", "-dilM", "-dilM", "-dilM",
    "-dilM", "-dilM", "-dilM", "-dilM", "-dilM", "-dilM",
    ref_dil
])

ref_mask = TEMP_DIR / "ref_mask.nii.gz"
run(["fslmaths", ref_dil, "-bin", "-fillh", ref_mask])

image_files = sorted([f for ext in ["*.nii", "*.nii.gz"] for f in INPUT_DIR.glob(ext)])

for img in image_files:
    if not any(m.upper() in img.name.upper() for m in MODALITIES): continue

    base = get_name(img)
    
    patient_reoriented = TEMP_DIR / f"{base}_reoriented.nii.gz"
    mat_reorient = TEMP_DIR / f"{base}_reorient.mat"
    
    run(["fslreorient2std", "-m", mat_reorient, img, patient_reoriented])
    run(["fslorient", "-copysform2qform", patient_reoriented])
    
    patient_cropped_for_calc = TEMP_DIR / f"{base}_cropped.nii.gz"
    patient_brain_for_calc = TEMP_DIR / f"{base}_brain_calc.nii.gz"
    mat_crop_to_full = TEMP_DIR / f"{base}_crop_to_full.mat"
    
    run(["robustfov", "-i", patient_reoriented, "-r", patient_cropped_for_calc, "-m", mat_crop_to_full])
    run(["bet", patient_cropped_for_calc, patient_brain_for_calc, "-R", "-f", "0.5"])
    
    mat_crop_to_ref = TEMP_DIR / f"{base}_crop_to_ref.mat"
    run(["flirt", "-in", patient_brain_for_calc, "-ref", ref_brain, "-omat", mat_crop_to_ref, "-dof", "12"])
    
    mat_ref_to_crop = TEMP_DIR / f"{base}_ref_to_crop.mat"
    run(["convert_xfm", "-omat", mat_ref_to_crop, "-inverse", mat_crop_to_ref])
    
    mat_ref_to_full = TEMP_DIR / f"{base}_ref_to_full.mat"
    run(["convert_xfm", "-omat", mat_ref_to_full, "-concat", mat_crop_to_full, mat_ref_to_crop])
    
    mask_reoriented = TEMP_DIR / f"{base}_mask_reoriented.nii.gz"
    run(["flirt", "-in", ref_mask, "-ref", patient_reoriented, "-applyxfm", "-init", mat_ref_to_full, "-out", mask_reoriented, "-interp", "nearestneighbour"])

    mat_unreorient = TEMP_DIR / f"{base}_unreorient.mat"
    run(["convert_xfm", "-omat", mat_unreorient, "-inverse", mat_reorient])
    
    mask_raw_space = TEMP_DIR / f"{base}_mask_raw.nii.gz"
    run(["flirt", "-in", mask_reoriented, "-ref", img, "-applyxfm", "-init", mat_unreorient, "-out", mask_raw_space, "-interp", "nearestneighbour"])

    masked_raw = TEMP_DIR / f"{base}_masked_raw.nii.gz"
    run(["fslmaths", img, "-mas", mask_raw_space, masked_raw])

    final_out = IMAGES_TS_DIR / f"{base}_0000.nii.gz"
    
    swap_cmd = ["fslswapdim", str(masked_raw), "AP", "IS", "LR", str(final_out)]
    print(f">>> {' '.join(swap_cmd)}")
    
    if not DRY_RUN:
        result = subprocess.run(swap_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            combined_output = result.stdout + "\n" + result.stderr
            if "Try the following command instead:" in combined_output:
                for line in combined_output.split('\n'):
                    if line.strip().startswith("fslswapdim"):
                        parts = line.strip().split()
                        safe_axes = parts[2:5]
                        
                        safe_swap_cmd = ["fslswapdim", str(masked_raw)] + safe_axes + [str(final_out)]
                        subprocess.run(safe_swap_cmd, check=True)
                        break
            else:
                print(combined_output)
                result.check_returncode()
