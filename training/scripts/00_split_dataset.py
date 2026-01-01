#!/usr/bin/env python3
"""
Split screenshots into training and test sets.
This ensures test data is never seen during training, giving realistic accuracy metrics.
"""

import sys
import shutil
import random
from pathlib import Path

def split_dataset(screenshots_dir, ground_truth_dir, test_ratio=0.2, seed=42):
    """
    Split dataset into train/test sets.

    Args:
        screenshots_dir: Directory with all screenshots
        ground_truth_dir: Directory with ground truth files
        test_ratio: Fraction to use for testing (default: 0.2 = 20%)
        seed: Random seed for reproducibility
    """
    screenshots_dir = Path(screenshots_dir)
    ground_truth_dir = Path(ground_truth_dir)

    # Create train/test directories
    train_screenshots = screenshots_dir.parent / "screenshots_train"
    train_gt = ground_truth_dir.parent / "ground_truth_train"
    test_screenshots = screenshots_dir.parent / "screenshots_test"
    test_gt = ground_truth_dir.parent / "ground_truth_test"

    for d in [train_screenshots, train_gt, test_screenshots, test_gt]:
        d.mkdir(parents=True, exist_ok=True)

    # Find all annotated pairs (screenshot + ground truth)
    gt_files = list(ground_truth_dir.glob("*.gt.txt"))

    if not gt_files:
        print(f"❌ No ground truth files found in {ground_truth_dir}")
        return

    # Match screenshots to ground truth
    pairs = []
    for gt_file in gt_files:
        img_name = gt_file.stem.replace('.gt', '')
        img_file = screenshots_dir / f"{img_name}.png"
        if not img_file.exists():
            img_file = screenshots_dir / f"{img_name}.jpg"
        if not img_file.exists():
            print(f"⚠️  No screenshot found for {gt_file.name}, skipping")
            continue
        pairs.append((img_file, gt_file))

    if not pairs:
        print("❌ No matching screenshot/ground-truth pairs found")
        return

    print(f"📊 Found {len(pairs)} annotated screenshot pairs")

    # Shuffle with seed for reproducibility
    random.seed(seed)
    random.shuffle(pairs)

    # Split
    split_idx = int(len(pairs) * (1 - test_ratio))
    train_pairs = pairs[:split_idx]
    test_pairs = pairs[split_idx:]

    print(f"📚 Training set: {len(train_pairs)} images ({(1-test_ratio)*100:.0f}%)")
    print(f"🧪 Test set: {len(test_pairs)} images ({test_ratio*100:.0f}%)")

    # Copy files
    print("\n📁 Copying training files...")
    for img_file, gt_file in train_pairs:
        shutil.copy2(img_file, train_screenshots / img_file.name)
        shutil.copy2(gt_file, train_gt / gt_file.name)

    print("📁 Copying test files...")
    for img_file, gt_file in test_pairs:
        shutil.copy2(img_file, test_screenshots / img_file.name)
        shutil.copy2(gt_file, test_gt / gt_file.name)

    # Create metadata file
    metadata = train_screenshots.parent / "dataset_split.txt"
    with open(metadata, 'w') as f:
        f.write(f"Dataset Split Information\n")
        f.write(f"========================\n\n")
        f.write(f"Total pairs: {len(pairs)}\n")
        f.write(f"Training pairs: {len(train_pairs)}\n")
        f.write(f"Test pairs: {len(test_pairs)}\n")
        f.write(f"Test ratio: {test_ratio}\n")
        f.write(f"Random seed: {seed}\n\n")

        f.write(f"Training files:\n")
        for img_file, _ in train_pairs:
            f.write(f"  - {img_file.name}\n")

        f.write(f"\nTest files:\n")
        for img_file, _ in test_pairs:
            f.write(f"  - {img_file.name}\n")

    print(f"\n✅ Dataset split complete!")
    print(f"\n📍 Directories created:")
    print(f"   Training screenshots: {train_screenshots}")
    print(f"   Training ground truth: {train_gt}")
    print(f"   Test screenshots: {test_screenshots}")
    print(f"   Test ground truth: {test_gt}")
    print(f"   Metadata: {metadata}")

    print(f"\n⚠️  IMPORTANT:")
    print(f"   - Use screenshots_train/ for training only")
    print(f"   - NEVER look at test data during training")
    print(f"   - Use screenshots_test/ only for final evaluation")

    # Update instructions
    print(f"\n📋 Next steps:")
    print(f"   1. Train model: ./00_quick_train.sh (will use screenshots_train/)")
    print(f"   2. Test model: python3 04_test_model.py ../screenshots_test/ ../ground_truth_test/")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Split dataset into train/test sets')
    parser.add_argument('--screenshots', default='../screenshots',
                        help='Directory with screenshots (default: ../screenshots)')
    parser.add_argument('--ground-truth', default='../ground_truth',
                        help='Directory with ground truth files (default: ../ground_truth)')
    parser.add_argument('--test-ratio', type=float, default=0.2,
                        help='Fraction for test set (default: 0.2 = 20%%)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility (default: 42)')

    args = parser.parse_args()

    split_dataset(args.screenshots, args.ground_truth, args.test_ratio, args.seed)
