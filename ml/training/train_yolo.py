"""Train YOLOv8 on the UrbanLens dataset."""

import argparse
from pathlib import Path

from ultralytics import YOLO


def train(
    data_config: str = "configs/yolo_train.yaml",
    model: str = "yolov8n.pt",
    epochs: int = 100,
    batch: int = 16,
    imgsz: int = 640,
    device: str = "cpu",
    project: str = "runs/train",
    name: str = "urbanlens_yolov8",
) -> None:
    """Fine-tune YOLOv8 on UrbanLens data."""
    model = YOLO(model)

    results = model.train(
        data=data_config,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        project=project,
        name=name,
        exist_ok=True,
        pretrained=True,
        optimizer="SGD",
        lr0=0.01,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=5.0,
        translate=0.1,
        scale=0.5,
        shear=2.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.0,
        patience=20,
    )

    print(f"Training complete. Results saved to {project}/{name}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Train YOLOv8 for UrbanLens")
    parser.add_argument("--data", default="configs/yolo_train.yaml")
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    train(
        data_config=args.data,
        model=args.model,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
    )


if __name__ == "__main__":
    main()
