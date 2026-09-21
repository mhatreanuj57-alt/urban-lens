"""Image embedder for duplicate detection."""

from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image


class ImageEmbedder:
    """Generate image embeddings for similarity search."""

    def __init__(self, model_name: str = "clip", device: str = "cpu"):
        """
        Initialize embedder.

        Args:
            model_name: 'clip' or 'siglip'
            device: 'cpu' or 'cuda'
        """
        self.device = device
        self.model_name = model_name
        self._model = None
        self._processor = None

    def _load_model(self):
        """Lazy-load the model."""
        if self._model is not None:
            return

        if self.model_name == "clip":
            from transformers import CLIPModel, CLIPProcessor

            self._model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self._processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        elif self.model_name == "siglip":
            from transformers import SiglipModel, SiglipProcessor

            self._model = SiglipModel.from_pretrained("google/siglip-base-patch16-224")
            self._processor = SiglipProcessor.from_pretrained("google/siglip-base-patch16-224")
        else:
            raise ValueError(f"Unknown model: {self.model_name}")

        self._model.to(self.device)
        self._model.eval()

    def embed(self, image: np.ndarray | str | Path) -> list[float]:
        """
        Generate embedding for an image.

        Args:
            image: numpy array, file path, or PIL Image

        Returns:
            Embedding vector as list of floats
        """
        self._load_model()

        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)

        inputs = self._processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            if self.model_name == "clip":
                outputs = self._model.get_image_features(**inputs)
            else:
                outputs = self._model.get_image_features(**inputs)

        embedding = outputs.cpu().numpy().flatten()
        # L2 normalize
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.tolist()

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """Cosine similarity between two embeddings."""
        a_arr = np.array(a)
        b_arr = np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))
