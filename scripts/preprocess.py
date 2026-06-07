#!/usr/bin/env python3
from pathlib import Path
import subprocess
import shutil

INPUT_DIR = Path("/input")
IMAGES_TS_DIR = Path("/app/imagesTs")
TEMP_DIR = Path("/app/temp_calc")
REF_IMAGE = Path("/app/resources/orion_reference_template.nii.gz")

MODALITIES = ["T1", "T2", "FLAIR"]
DRY_RUN = False

def run_cmd(cmd):
    cmd_str = [str(x) for x in cmd]
    if not DRY_RUN:
        subprocess.run(cmd_str, check=True, capture_output=True)

def get_base_name(p: Path) -> str:
    return p.name.replace(".nii.gz", "").replace(".nii", "")

def prepare_directories():
    if TEMP_DIR.exists(): shutil.rmtree(TEMP_DIR)
    IMAGES_TS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

def main():
    prepare_directories()

    print(">>> [1/2] Preparing ORION spatial bounding box template...")
    ref_std = TEMP_DIR / "ref_std.nii.gz"
    run_cmd(["fslreorient2std", REF_IMAGE, ref_std])

    ref_bin = TEMP_DIR / "ref_bin.nii.gz"
    run_cmd(["fslmaths", ref_std, "-bin", ref_bin])

    ref_dil = TEMP_DIR / "ref_dil.nii.gz"
    run_cmd([
        "fslmaths", ref_bin,
        "-dilM", "-dilM", "-dilM", "-dilM", "-dilM",
        "-dilM", "-dilM", "-dilM", "-dilM", "-dilM",
        "-dilM", "-dilM", "-dilM", "-dilM", "-dilM",
        ref_dil
    ])

    ref_mask = TEMP_DIR / "ref_mask.nii.gz"
    run_cmd(["fslmaths", ref_dil, "-subsamp2", "-subsamp2offc", "-bin", "-fillh", ref_mask])

    image_files = sorted([f for ext in ["*.nii", "*.nii.gz"] for f in INPUT_DIR.glob(ext)])
    print(f">>> [2/2] Processing {len(image_files)} input volume(s)...")

    for img in image_files:
        if not any(m.upper() in img.name.upper() for m in MODALITIES):
            continue

        base = get_base_name(img)
        print(f"    -> Standardizing: {img.name}")
        
        patient_reoriented = TEMP_DIR / f"{base}_reoriented.nii.gz"
        mat_reorient = TEMP_DIR / f"{base}_reorient.mat"
        run_cmd(["fslreorient2std", "-m", mat_reorient, img, patient_reoriented])
        run_cmd(["fslorient", "-copysform2qform", patient_reoriented])
        
        patient_cropped_for_calc = TEMP_DIR / f"{base}_cropped.nii.gz"
        patient_brain_for_calc = TEMP_DIR / f"{base}_brain_calc.nii.gz"
        mat_crop_to_full = TEMP_DIR / f"{base}_crop_to_full.mat"
        
        run_cmd(["robustfov", "-i", patient_reoriented, "-r", patient_cropped_for_calc, "-m", mat_crop_to_full])
        run_cmd(["bet", patient_cropped_for_calc, patient_brain_for_calc, "-R", "-f", "0.5"])
        
        mat_crop_to_ref = TEMP_DIR / f"{base}_crop_to_ref.mat"
        run_cmd(["flirt", "-in", patient_brain_for_calc, "-ref", ref_std, "-omat", mat_crop_to_ref, "-dof", "12"])
        
        mat_ref_to_crop = TEMP_DIR / f"{base}_ref_to_crop.mat"
        run_cmd(["convert_xfm", "-omat", mat_ref_to_crop, "-inverse", mat_crop_to_ref])
        
        mat_ref_to_full = TEMP_DIR / f"{base}_ref_to_full.mat"
        run_cmd(["convert_xfm", "-omat", mat_ref_to_full, "-concat", mat_crop_to_full, mat_ref_to_crop])
        
        mask_reoriented = TEMP_DIR / f"{base}_mask_reoriented.nii.gz"
        run_cmd(["flirt", "-in", ref_mask, "-ref", patient_reoriented, "-applyxfm", "-init", mat_ref_to_full, "-out", mask_reoriented, "-interp", "nearestneighbour"])

        mat_unreorient = TEMP_DIR / f"{base}_unreorient.mat"
        run_cmd(["convert_xfm", "-omat", mat_unreorient, "-inverse", mat_reorient])
        
        mask_raw_space = TEMP_DIR / f"{base}_mask_raw.nii.gz"
        run_cmd(["flirt", "-in", mask_reoriented, "-ref", img, "-applyxfm", "-init", mat_unreorient, "-out", mask_raw_space, "-interp", "nearestneighbour"])

        final_out = IMAGES_TS_DIR / f"{base}_0000.nii.gz"
        run_cmd(["fslmaths", img, "-mas", mask_raw_space, final_out])

    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
        
    print(">>> Preprocessing complete. Ready for inference.")

if __name__ == "__main__":
    main()
