# ORION Clinical Pipeline v1.0

ORION is an automated, containerized deep learning pipeline for medical image segmentation. It integrates robust spatial preprocessing (via FSL) and advanced 3D volumetric inference (via nnU-Net v2) into a single, seamless Docker workflow. 

This pipeline is fully optimized to run on CPU environments (including Apple Silicon via AMD64 emulation), ensuring high accessibility without requiring dedicated NVIDIA GPUs.

---

## 🚀 Features
* **Automated Preprocessing:** Integrates FSL tools (`fslreorient2std`, `robustfov`, `bet`, `flirt`) to standardize spatial bounding boxes, extract brain tissue, and align inputs to a standard reference template.
* **Deep Learning Inference:** Utilizes nnU-Net v2 for state-of-the-art 3D biomedical image segmentation.
* **Non-Destructive Workflow:** Safely isolates raw patient data from intermediate processing calculations.
* **Plug-and-Play:** Containerized via Docker, eliminating local dependency conflicts.

---

## 📋 Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
* Pre-trained nnU-Net model weights.

---

## 🛠️ Installation

Clone this repository and build the Docker image. The build process will automatically download Ubuntu 22.04, install FSL, and set up all Python dependencies (including PyTorch and nnU-Net).

```
git clone https://github.com/your-username/orion-pipeline.git
cd orion-pipeline
docker build -t orion-pipeline .
```

## 📂 Directory Structure Setup

Before running the pipeline, ensure you have the following directories created on your local machine:

1. `input_data/`: Contains your raw NIfTI files. 
   * *Requirement:* Files **must** include the modality (T1, T2, or FLAIR) and follow the nnU-Net naming convention by ending with `_0000.nii.gz` (e.g., `Patient01_T1_0000.nii.gz`).
2. `output_data/`: An empty directory where the final segmentations will be saved.
3. `weights/`: Contains your pre-trained nnU-Net model.

---

## 🖥️ Usage

Run the pipeline using the following command. Replace the `/local/path/to/...` placeholders with the absolute paths on your machine.

```bash
docker run --rm \
  -v /local/path/to/weights:/weights \
  -v /local/path/to/input_data:/input \
  -v /local/path/to/output_data:/output \
  orion-pipeline
```

### What happens during execution?
* **[PHASE 1] Preprocessing:** The pipeline scans the `/input` directory, applies FSL transformations to standardize the volumes, applies a spatial bounding box, and saves the prepared files into `/app/imagesTs`.
* **[PHASE 2] Inference:** nnU-Net detects the processed files and executes the model prediction entirely on the CPU.
* **Post-processing:** The resulting segmentations are written to your local `/output` directory, prefixed with `orion_`.

### ⚡ Performance Tuning
By default, ORION is configured for **maximum stability** (`-npp 0 -nps 0`), which consumes minimal RAM and ensures the pipeline works on most standard workstations. 

If you are running ORION on a high-end server with significant RAM (e.g., 32GB+), you can increase processing speed by modifying `scripts/predict.py` and setting `-npp` and `-nps` to a higher value (e.g., `4` or `8`) to enable parallel processing.
 
---

## 🧠 Segmentation Labels
The model output consists of integer labels representing specific anatomical structures defined in the `dataset.json` file. The mapping is as follows:

| Label | Anatomical Structure |
| :--- | :--- |
| 0 | Background |
| 1 | CSF |
| 2 | Outer CSF |
| 3 | Basal Ganglia |
| 4 | Cortex / Cerebellum |
| 5 | White Matter (WM) |
| 6 | Muscle |
| 7 | Fat |
| 8 | Vessels / Choroid |
| 9 | Optic Nerve (ON) |
| 10 | Chiasm |
| 11 | Optic Tract |
| 12 | Globe |


---


## 📝 License & Citations

If you use the ORION pipeline in your research or clinical workflow, **please cite our clinical review article** to acknowledge the foundational research behind this tool:

* **Clinical Context / ORION:** Xena-Bosch, C., Kodali, S., Sahib, N., Chard, D., Llufriu, S., Toosy, A. T., Martinez-Heras, E., & Prados, F. (2025). Advances in MRI optic nerve segmentation. *Multiple Sclerosis and Related Disorders*, 98, 106437. https://doi.org/10.1016/j.msard.2025.106437

Additionally, please ensure you cite the foundational open-source tools this pipeline relies upon:

* **nnU-Net:** Isensee, F., Jaeger, P. F., Kohl, S. A., Petersen, J., & Maier-Hein, K. H. (2021). *nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation.* Nature methods, 18(2), 203-211.
* **FSL:** Jenkinson, M., Beckmann, C. F., Behrens, T. E., Woolrich, M. W., & Smith, S. M. (2012). *FSL.* Neuroimage, 62(2), 782-790.
