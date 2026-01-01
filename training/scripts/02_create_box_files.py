#!/usr/bin/env python3
"""
Generate Tesseract box files from screenshots and ground truth.
Box files contain character-level bounding boxes needed for training.
"""

import sys
import subprocess
from pathlib import Path

def create_box_files(screenshots_dir, ground_truth_dir, output_dir, lang="eng"):
    """
    Create .box files using Tesseract's batch mode.

    The .box file format:
    <character> <left> <bottom> <right> <top> <page>
    """
    screenshots_dir = Path(screenshots_dir)
    ground_truth_dir = Path(ground_truth_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all ground truth files
    gt_files = sorted(ground_truth_dir.glob("*.gt.txt"))

    if not gt_files:
        print(f"❌ No ground truth files found in {ground_truth_dir}")
        return

    print(f"📦 Creating box files for {len(gt_files)} images...")

    for idx, gt_file in enumerate(gt_files, 1):
        # Find corresponding image
        img_name = gt_file.stem.replace('.gt', '')
        img_file = screenshots_dir / f"{img_name}.png"

        if not img_file.exists():
            img_file = screenshots_dir / f"{img_name}.jpg"

        if not img_file.exists():
            print(f"⚠️  [{idx}/{len(gt_files)}] Image not found: {img_name}")
            continue

        # Output paths (Tesseract requires specific naming)
        base_name = f"vri.{img_name}"
        tif_file = output_dir / f"{base_name}.tif"
        box_file = output_dir / f"{base_name}.box"

        # Convert image to TIFF (required for training)
        try:
            from PIL import Image
            img = Image.open(img_file)
            img.save(tif_file, format='TIFF')
        except Exception as e:
            print(f"❌ [{idx}/{len(gt_files)}] Failed to convert {img_name}: {e}")
            continue

        # Generate initial box file using Tesseract
        try:
            cmd = [
                "tesseract",
                str(tif_file),
                str(output_dir / base_name),
                "-l", lang,
                "batch.nochop",
                "makebox"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ [{idx}/{len(gt_files)}] Created: {box_file.name}")
        except subprocess.CalledProcessError as e:
            print(f"❌ [{idx}/{len(gt_files)}] Tesseract error: {e.stderr.decode()}")
        except FileNotFoundError:
            print("❌ Tesseract not found. Please install: sudo apt-get install tesseract-ocr")
            return

    print(f"\n✨ Box files created in {output_dir}")
    print("\n⚠️  IMPORTANT: Manual correction required!")
    print("Box files contain auto-generated character positions.")
    print("You must manually verify and correct them using a tool like:")
    print("  - jTessBoxEditor (Java GUI)")
    print("  - BoxEditor (Python)")
    print("  - qt-box-editor (Qt GUI)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python 02_create_box_files.py <screenshots_dir> <ground_truth_dir>")
        print("Example: python 02_create_box_files.py ../screenshots ../ground_truth")
        sys.exit(1)

    screenshots_dir = sys.argv[1]
    ground_truth_dir = sys.argv[2]
    output_dir = "../box_files"

    create_box_files(screenshots_dir, ground_truth_dir, output_dir)
