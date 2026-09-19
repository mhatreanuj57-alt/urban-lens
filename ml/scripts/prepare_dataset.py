"""Prepare UrbanLens dataset for training."""

import argparse
import shutil
from pathlib import Path
from random import shuffle


def prepare_dataset(
    source_dir: str,
    output_dir: str = "data/urbanlens",
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> None:
    """
    Split dataset into train/val/test directories.

    Expected source structure:
        source_dir/
        ├── images/
        │   ├── img001.jpg
        │   └── ...
        └── labels/
            ├── img001.txt
            └── ...
    """
    source = Path(source_dir)
    output = Path(output_dir)

    images_dir = source / "images"
    labels_dir = source / "labels"

    if not images_dir.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")
    if not labels_dir.exists():
        raise FileNotFoundError(f"Labels directory not found: {labels_dir}")

    # Get all image files
    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    images = [f for f in images_dir.iterdir() if f.suffix.lower() in image_extensions]
    images.sort()

    # Shuffle with seed
    import random
    random.seed(seed)
    shuffle(images)

    # Calculate split indices
    n = len(images)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)

    splits = {
        "train": images[:train_end],
        "val": images[train_end:val_end],
        "test": images[val_end:],
    }

    # Create output directories
    for split_name, split_images in splits.items():
        img_out = output / "images" / split_name
        lbl_out = output / "labels" / split_name
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        for img_path in split_images:
            # Copy image
            shutil.copy2(img_path, img_out / img_path.name)

            # Copy corresponding label
            label_path = labels_dir / f"{img_path.stem}.txt"
            if label_path.exists():
                shutil.copy2(label_path, lbl_out / label_path.name)

        print(f"{split_name}: {len(split_images)} images")

    print(f"\nDataset prepared at {output}")
    print(f"Total: {n} images")


def main():
    parser = argparse.ArgumentParser(description="Prepare UrbanLens dataset")
    parser.add_argument("--source", required=True, help="Source directory with images/ and labels/")
    parser.add_argument("--output", default="data/urbanlens", help="Output directory")
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    prepare_dataset(
        source_dir=args.source,
        output_dir=args.output,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
