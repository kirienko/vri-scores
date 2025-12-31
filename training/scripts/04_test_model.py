#!/usr/bin/env python3
"""
Test the trained VRI model against test screenshots and compare accuracy.
"""

import sys
from pathlib import Path
import pytesseract
from PIL import Image

def test_model(test_dir, ground_truth_dir, model_name="vri"):
    """
    Test the custom model vs. default English model.
    Calculate accuracy metrics.
    """
    test_dir = Path(test_dir)
    ground_truth_dir = Path(ground_truth_dir)

    # Find test images
    test_images = sorted(test_dir.glob("*.png")) + sorted(test_dir.glob("*.jpg"))

    if not test_images:
        print(f"❌ No test images found in {test_dir}")
        return

    print(f"🧪 Testing {len(test_images)} images")
    print("=" * 80)

    results = {
        'total': 0,
        'custom_correct': 0,
        'base_correct': 0,
        'both_correct': 0,
        'both_wrong': 0
    }

    for img_path in test_images:
        # Load ground truth
        gt_file = ground_truth_dir / f"{img_path.stem}.gt.txt"
        if not gt_file.exists():
            print(f"⚠️  No ground truth for {img_path.name}, skipping")
            continue

        ground_truth = gt_file.read_text(encoding='utf-8').strip()

        # OCR with both models
        img = Image.open(img_path)

        try:
            text_custom = pytesseract.image_to_string(img, lang=model_name).strip()
        except Exception as e:
            print(f"❌ Custom model error: {e}")
            print(f"   Make sure {model_name}.traineddata is in tessdata directory")
            return

        text_base = pytesseract.image_to_string(img, lang='eng').strip()

        # Compare
        custom_match = text_custom == ground_truth
        base_match = text_base == ground_truth

        results['total'] += 1
        if custom_match:
            results['custom_correct'] += 1
        if base_match:
            results['base_correct'] += 1
        if custom_match and base_match:
            results['both_correct'] += 1
        if not custom_match and not base_match:
            results['both_wrong'] += 1

        # Show detailed comparison for failures
        if not custom_match:
            print(f"\n📸 {img_path.name}")
            print(f"✅ Ground truth:\n{ground_truth}\n")
            print(f"🔧 Custom model ({model_name}):")
            print(f"{text_custom}\n")
            print(f"📖 Base model (eng):")
            print(f"{text_base}\n")
            print("-" * 80)

    # Summary
    print("\n" + "=" * 80)
    print("📊 RESULTS SUMMARY")
    print("=" * 80)

    if results['total'] == 0:
        print("❌ No tests run (missing ground truth files)")
        return

    custom_accuracy = (results['custom_correct'] / results['total']) * 100
    base_accuracy = (results['base_correct'] / results['total']) * 100
    improvement = custom_accuracy - base_accuracy

    print(f"Total images tested: {results['total']}")
    print(f"\nCustom model ({model_name}): {results['custom_correct']}/{results['total']} correct ({custom_accuracy:.1f}%)")
    print(f"Base model (eng):     {results['base_correct']}/{results['total']} correct ({base_accuracy:.1f}%)")
    print(f"\n{'📈' if improvement > 0 else '📉'} Improvement: {improvement:+.1f}%")
    print(f"\nBoth correct:  {results['both_correct']}")
    print(f"Both wrong:    {results['both_wrong']}")
    print(f"Only custom:   {results['custom_correct'] - results['both_correct']}")
    print(f"Only base:     {results['base_correct'] - results['both_correct']}")

    # Recommendations
    print("\n" + "=" * 80)
    if improvement > 10:
        print("✅ Excellent! Custom model shows significant improvement.")
        print("   Deploy this model to production.")
    elif improvement > 0:
        print("👍 Good! Custom model is better.")
        print("   Consider collecting more training data for further improvement.")
    else:
        print("⚠️  Custom model is not better than base model.")
        print("   Possible issues:")
        print("   - Not enough training data (need 50+ diverse examples)")
        print("   - Box file corrections incomplete")
        print("   - Training iterations too low/high")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python 04_test_model.py <test_images_dir> <ground_truth_dir> [model_name]")
        print("Example: python 04_test_model.py ../screenshots/test ../ground_truth/test vri")
        sys.exit(1)

    test_dir = sys.argv[1]
    ground_truth_dir = sys.argv[2]
    model_name = sys.argv[3] if len(sys.argv) > 3 else "vri"

    test_model(test_dir, ground_truth_dir, model_name)
