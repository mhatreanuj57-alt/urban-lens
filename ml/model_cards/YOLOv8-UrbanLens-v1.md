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

- 300–500 images collected locally with consent
- Annotated in YOLO format
- Augmentation: mosaic, flip, color jitter

## Metrics

| Metric | Value |
| --- | --- |
| mAP@50 | 0.70+ |
| Precision | TBD |
| Recall | TBD |

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
