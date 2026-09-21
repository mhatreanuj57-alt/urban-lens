# UrbanLens AI — ML

Machine learning code for training, inference, and model cards.

## Structure

```
├── training/        YOLO fine-tuning scripts
├── inference/       Runtime detection and embedding
├── model_cards/     Model documentation
├── configs/         Training configs (YOLO, LightGBM)
├── notebooks/       Exploration notebooks
└── scripts/         Data processing and evaluation
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r ../backend/requirements.txt
pip install ultralytics torch torchvision
```

## Train the detector (no local GPU needed — use Google Colab)

You do not need a GPU on this machine. Train on a free Colab GPU and copy the weights back.

1. Open **`notebooks/urbanlens_colab_train.ipynb`** in Google Colab.
2. **Runtime ▸ Change runtime type ▸ T4 GPU.**
3. In the **Config** cell paste your free Roboflow API key and a public dataset's
   workspace/project/version. Public data is uneven across the 5 classes, so start with a
   **pothole** dataset (e.g. search *pothole detection* on Roboflow Universe) and set
   `CLASS_NAMES = ['pothole']`. Add the other classes later as more data is collected.
4. Run all cells. It trains, evaluates (mAP), shows sample detections, then downloads
   `urbanlens_yolov8_v1.pt` and a filled-in `model_card.md`.

### Deploy the model locally

1. Put the downloaded weights into `ml/models/` (weights are gitignored):
   ```
   ml/models/urbanlens_yolov8_v1.pt
   ```
   The backend loads the first `*.pt` found in that folder (`settings.ML_MODEL_PATH`).
2. Install the ML runtime into the backend venv so inference can actually run:
   ```bash
   backend/.venv/Scripts/python.exe -m pip install ultralytics torch torchvision
   ```
3. Restart the API and submit a report — the pipeline now runs real detection instead of the
   `model_weights_not_available` fallback. The model's class names flow straight into the UI
   labels, so keep them aligned with `pothole` / `garbage` / `damaged_streetlight` /
   `waterlogging` / `illegal_dumping`.

> Detection currently skips gracefully when `ultralytics` or the weights are missing; blur and
> embedding (perceptual-hash fallback) still run. Copying weights in + installing ultralytics
> turns on real detection with no code changes.

