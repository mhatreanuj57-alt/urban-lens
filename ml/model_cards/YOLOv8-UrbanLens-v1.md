# YOLOv8-UrbanLens v1

## Model description

YOLOv8 fine-tuned on the UrbanLens dataset for detecting civic issues in Navi Mumbai.

## Classes

| Class | ID | Description |
| --- | --- | --- |
| pothole | 0 | Road surface damage |
| garbage | 1 | Illegal waste accumulation |
| damaged_streetlight | 2 | Broken or non-functional street lighting |
| waterlogging | 3 | Standing water on roads |
| illegal_dumping | 4 | Unauthorized waste disposal |

## Training data

- Source: public Hugging Face dataset `Ryukijano/Pothole-detection-Yolov8` (YOLO format, single class `pothole`, ~880 images)
- Base model: `yolov8n.pt`, epochs=60, imgsz=640, seed=42, trained on Google Colab T4
- v1 is pothole-focused; other UrbanLens classes (garbage, damaged_streetlight, waterlogging, illegal_dumping) to be added as more data is collected

## Metrics

| Metric | Value |
| --- | --- |
| mAP@50 | 0.330 |
| mAP@50-95 | 0.154 |
| Precision | 0.644 |
| Recall | 0.255 |

## Limitations

- Trained on Navi Mumbai imagery only
- Performance degrades in heavy rain or low light
- Not suitable for safety-critical applications

## Ethical considerations

- Faces and number plates are blurred in public outputs
- Training consent obtained from all contributors
- Model is decision-support only, not a replacement for inspection

## Citation

```
@software{urbanlens_yolov8_2026,
  title = {YOLOv8-UrbanLens v1},
  author = {UrbanLens AI Contributors},
  year = {2026},
  url = {https://github.com/a18-n03/Urban-Lens}
}
```
