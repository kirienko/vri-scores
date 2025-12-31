#!/usr/bin/env python3
"""
Interactive tool to create ground truth annotations for screenshots.
Displays each image and lets you type the correct text.
"""

import sys
import os
from pathlib import Path
from PIL import Image

def create_ground_truth(screenshots_dir, ground_truth_dir):
    """Interactive ground truth creation"""
    screenshots_dir = Path(screenshots_dir)
    ground_truth_dir = Path(ground_truth_dir)
    ground_truth_dir.mkdir(parents=True, exist_ok=True)

    # Find all screenshots
    image_files = sorted(screenshots_dir.glob("*.png")) + sorted(screenshots_dir.glob("*.jpg"))

    if not image_files:
        print(f"❌ No images found in {screenshots_dir}")
        return

    print(f"📸 Found {len(image_files)} screenshots")
    print("=" * 60)
    print("Instructions:")
    print("1. Each image will be displayed in your system viewer")
    print("2. Type the EXACT text visible in the ranking")
    print("3. Type 'skip' to skip an image")
    print("4. Type 'quit' to exit")
    print("=" * 60)

    for idx, img_path in enumerate(image_files, 1):
        gt_path = ground_truth_dir / f"{img_path.stem}.gt.txt"

        # Skip if already annotated
        if gt_path.exists():
            print(f"[{idx}/{len(image_files)}] ✓ Already annotated: {img_path.name}")
            continue

        print(f"\n[{idx}/{len(image_files)}] 🖼️  {img_path.name}")

        # Open image in system viewer
        try:
            img = Image.open(img_path)
            img.show()
        except Exception as e:
            print(f"⚠️  Could not display image: {e}")

        print("\nEnter the ranking text (one line per entry):")
        print("Example: 1 - PlayerName")
        print("When done, enter a blank line, 'skip', or 'quit'")
        print("-" * 40)

        lines = []
        while True:
            line = input()
            if line.lower() == 'quit':
                print("👋 Exiting...")
                return
            if line.lower() == 'skip':
                print("⏭️  Skipped")
                break
            if not line.strip():
                if lines:  # Blank line signals end of entry
                    break
                else:
                    continue
            lines.append(line)

        if lines:
            # Save ground truth
            gt_text = '\n'.join(lines)
            gt_path.write_text(gt_text, encoding='utf-8')
            print(f"✅ Saved: {gt_path.name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python 01_prepare_ground_truth.py <screenshots_dir>")
        print("Example: python 01_prepare_ground_truth.py ../screenshots")
        sys.exit(1)

    screenshots_dir = sys.argv[1]
    ground_truth_dir = "../ground_truth"

    create_ground_truth(screenshots_dir, ground_truth_dir)
    print("\n✨ Ground truth preparation complete!")
