"""Object detection with ONNX Runtime — no torch required.

The deployed container installs `onnxruntime` only. Torch + ultralytics cost
several hundred MB of RAM that a free hosting tier cannot hold, while the
exported YOLOv8 graph needs neither: everything below is numpy + Pillow, so
detection runs on a 512 MB instance.

`detect()` returns the detection list, or None when no model can be loaded —
callers must treat None as "detection unavailable", not "nothing found".
"""

import ast
import logging
from pathlib import Path

import numpy as np
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)

IMG_SIZE = 640
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.45

_session = None
_session_loaded = False
MODEL_NAME = "yolov8-urbanlens"


def _load_session():
    """Create the ORT session once; None means detection is unavailable."""
    global _session, _session_loaded, MODEL_NAME
    if _session_loaded:
        return _session
    _session_loaded = True
    try:
        import onnxruntime as ort

        path = sorted(Path(settings.ML_MODEL_PATH).glob("*.onnx"))
        if not path:
            raise RuntimeError(f"no .onnx model found in {settings.ML_MODEL_PATH}")
        _session = ort.InferenceSession(str(path[0]), providers=["CPUExecutionProvider"])
        metadata = _session.get_modelmeta().custom_metadata_map or {}
        _session.urbanlens_names = _parse_names(metadata.get("names"))
        MODEL_NAME = path[0].stem
        logger.info("ONNX detector loaded %s (%s classes)", path[0].name, len(_session.urbanlens_names))
    except Exception as exc:  # optional dependency or absent weights
        logger.info("ONNX detector unavailable: %s", exc)
    return _session


def _parse_names(raw: str | None) -> dict[int, str]:
    """Ultralytics stores class names in ONNX metadata as a python dict literal."""
    if not raw:
        return {}
    try:
        return {int(k): str(v) for k, v in ast.literal_eval(raw).items()}
    except (ValueError, SyntaxError, TypeError):
        return {}


def _letterbox(img: Image.Image) -> tuple[np.ndarray, float, int, int]:
    """Scale onto a square canvas, returning the CHW blob and its transform."""
    ratio = min(IMG_SIZE / img.width, IMG_SIZE / img.height)
    new_w, new_h = round(img.width * ratio), round(img.height * ratio)
    pad_x, pad_y = (IMG_SIZE - new_w) // 2, (IMG_SIZE - new_h) // 2
    try:  # cv2 resizes like ultralytics trained with; Pillow is the fallback
        import cv2

        arr = cv2.copyMakeBorder(
            cv2.resize(np.asarray(img), (new_w, new_h), interpolation=cv2.INTER_LINEAR),
            pad_y, IMG_SIZE - new_h - pad_y, pad_x, IMG_SIZE - new_w - pad_x,
            cv2.BORDER_CONSTANT, value=(114, 114, 114),
        )
    except ImportError:
        canvas = Image.new("RGB", (IMG_SIZE, IMG_SIZE), (114, 114, 114))
        canvas.paste(img.resize((new_w, new_h), Image.BILINEAR), (pad_x, pad_y))
        arr = np.asarray(canvas)
    return np.ascontiguousarray(arr.astype(np.float32).transpose(2, 0, 1)[None]) / 255.0, ratio, pad_x, pad_y


def _nms(boxes: np.ndarray, scores: np.ndarray) -> list[int]:
    """Greedy NMS within one class, highest confidence first."""
    keep: list[int] = []
    order = scores.argsort()[::-1]
    while order.size:
        i = int(order[0])
        keep.append(i)
        if order.size == 1:
            break
        rest = boxes[order[1:]]
        ix = np.clip(np.minimum(boxes[i, 2], rest[:, 2]) - np.maximum(boxes[i, 0], rest[:, 0]), 0, None)
        iy = np.clip(np.minimum(boxes[i, 3], rest[:, 3]) - np.maximum(boxes[i, 1], rest[:, 1]), 0, None)
        inter = ix * iy
        union = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])
        union = union + (rest[:, 2] - rest[:, 0]) * (rest[:, 3] - rest[:, 1]) - inter
        iou = np.where(union > 1e-9, inter / union, 1.0)
        order = order[1:][iou <= IOU_THRESHOLD]
    return keep


def _unscale(box: np.ndarray, ratio: float, pad_x: int, pad_y: int, w: int, h: int) -> list[float]:
    """Map a letterboxed box back onto the original image, clipped to its edges."""
    x1, y1, x2, y2 = ((box[0] - pad_x) / ratio, (box[1] - pad_y) / ratio,
                      (box[2] - pad_x) / ratio, (box[3] - pad_y) / ratio)
    return [
        round(float(np.clip(x1, 0, w)), 1),
        round(float(np.clip(y1, 0, h)), 1),
        round(float(np.clip(x2, 0, w)), 1),
        round(float(np.clip(y2, 0, h)), 1),
    ]


def detect(img: Image.Image) -> list[dict] | None:
    """Run the detector on a PIL image, returning boxes in original pixels."""
    session = _load_session()
    if session is None:
        return None

    blob, ratio, pad_x, pad_y = _letterbox(img)
    # YOLOv8 emits [1, 4 + n_classes, n_anchors] as centre x/y, width, height in
    # letterboxed pixels, with sigmoid-applied scores.
    predictions = np.squeeze(session.run(None, {session.get_inputs()[0].name: blob})[0]).T
    cx, cy, w, h = predictions[:, 0], predictions[:, 1], predictions[:, 2], predictions[:, 3]
    boxes = np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], axis=1)
    class_ids = predictions[:, 4:].argmax(1)
    scores = predictions[:, 4:].max(1)

    detections: list[dict] = []
    for cls in np.unique(class_ids[scores > CONF_THRESHOLD]):
        selected = (class_ids == cls) & (scores > CONF_THRESHOLD)
        cand_boxes, cand_scores = boxes[selected], scores[selected]
        for i in _nms(cand_boxes, cand_scores):
            detections.append({
                "bbox": _unscale(cand_boxes[i], ratio, pad_x, pad_y, img.width, img.height),
                "class_id": int(cls),
                "class_name": session.urbanlens_names.get(int(cls), f"class_{int(cls)}"),
                "confidence": round(float(cand_scores[i]), 3),
            })
    return detections
