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
