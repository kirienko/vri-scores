#!/usr/bin/env python3
"""
Comprehensive evaluation script for trained VRI OCR model.
Tests on UNSEEN data and provides detailed metrics.
"""

import sys
from pathlib import Path
import pytesseract
from PIL import Image
import json
from collections import defaultdict

# Add parent directory to import extract module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from extract import preprocess_image_from_bytes, parse_rankings_from_text

def levenshtein_distance(s1, s2):
    """Calculate edit distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def evaluate_model(test_screenshots_dir, test_ground_truth_dir, model_name="vri", baseline_model="eng"):
    """
    Comprehensive evaluation on test set (unseen during training).

    Metrics:
    - Position detection accuracy (did we find rank 11?)
    - Name extraction accuracy (exact match)
    - Character-level accuracy (edit distance)
    - Problem case analysis (where does it fail?)
    """
    test_screenshots_dir = Path(test_screenshots_dir)
    test_ground_truth_dir = Path(test_ground_truth_dir)

    test_images = sorted(test_screenshots_dir.glob("*.png")) + sorted(test_screenshots_dir.glob("*.jpg"))

    if not test_images:
        print(f"❌ No test images found in {test_screenshots_dir}")
        return

    print("=" * 80)
    print(f"🧪 COMPREHENSIVE OCR MODEL EVALUATION")
    print("=" * 80)
    print(f"\nTest set: {len(test_images)} images (UNSEEN during training)")
    print(f"Custom model: {model_name}")
    print(f"Baseline model: {baseline_model}")
    print("=" * 80)

    # Metrics tracking
    metrics = {
        'custom': defaultdict(int),
        'baseline': defaultdict(int)
    }

    problem_cases = {
        'custom': [],
        'baseline': []
    }

    position_11_stats = {
        'total_with_11': 0,
        'custom_detected': 0,
        'baseline_detected': 0
    }

    for img_path in test_images:
        gt_file = test_ground_truth_dir / f"{img_path.stem}.gt.txt"
        if not gt_file.exists():
            print(f"⚠️  No ground truth for {img_path.name}, skipping")
            continue

        # Parse ground truth
        gt_text = gt_file.read_text(encoding='utf-8')
        gt_rankings = parse_rankings_from_text(gt_text)

        # Load and preprocess image
        with open(img_path, 'rb') as f:
            image_bytes = f.read()

        preprocessed_img = preprocess_image_from_bytes(image_bytes)

        # OCR with both models
        try:
            text_custom = pytesseract.image_to_string(preprocessed_img, lang=model_name)
            rankings_custom = parse_rankings_from_text(text_custom)
        except Exception as e:
            print(f"❌ Custom model error on {img_path.name}: {e}")
            continue

        try:
            text_baseline = pytesseract.image_to_string(preprocessed_img, lang=baseline_model)
            rankings_baseline = parse_rankings_from_text(text_baseline)
        except Exception as e:
            print(f"❌ Baseline model error on {img_path.name}: {e}")
            continue

        # Check if ground truth has position 11
        if 11 in gt_rankings:
            position_11_stats['total_with_11'] += 1
            if 11 in rankings_custom:
                position_11_stats['custom_detected'] += 1
            if 11 in rankings_baseline:
                position_11_stats['baseline_detected'] += 1

        # Evaluate both models
        for model_type, rankings in [('custom', rankings_custom), ('baseline', rankings_baseline)]:
            metrics[model_type]['total_images'] += 1

            # Position detection accuracy
            gt_positions = set(gt_rankings.keys())
            detected_positions = set(rankings.keys())

            correct_positions = gt_positions & detected_positions
            missing_positions = gt_positions - detected_positions
            false_positions = detected_positions - gt_positions

            metrics[model_type]['positions_detected'] += len(correct_positions)
            metrics[model_type]['positions_total'] += len(gt_positions)
            metrics[model_type]['positions_missed'] += len(missing_positions)
            metrics[model_type]['positions_false'] += len(false_positions)

            # Name extraction accuracy (for correctly detected positions)
            for position in correct_positions:
                gt_name = gt_rankings[position]
                detected_name = rankings[position]

                if gt_name == detected_name:
                    metrics[model_type]['names_exact_match'] += 1
                else:
                    # Calculate character-level accuracy
                    edit_dist = levenshtein_distance(gt_name, detected_name)
                    metrics[model_type]['names_total_edit_distance'] += edit_dist

                    # Track problem case
                    problem_cases[model_type].append({
                        'image': img_path.name,
                        'position': position,
                        'expected': gt_name,
                        'got': detected_name,
                        'edit_distance': edit_dist
                    })

                metrics[model_type]['names_total'] += 1

            # Perfect extraction (all positions + all names correct)
            if detected_positions == gt_positions:
                all_names_correct = all(
                    rankings[pos] == gt_rankings[pos]
                    for pos in gt_positions
                )
                if all_names_correct:
                    metrics[model_type]['perfect_extractions'] += 1

    # Print results
    print("\n" + "=" * 80)
    print("📊 RESULTS")
    print("=" * 80)

    for model_type in ['custom', 'baseline']:
        m = metrics[model_type]
        model_label = f"{model_name}" if model_type == 'custom' else f"{baseline_model} (baseline)"

        print(f"\n{'─' * 80}")
        print(f"📈 {model_label.upper()}")
        print(f"{'─' * 80}")

        # Overall metrics
        print(f"\n🎯 Overall Performance:")
        perfect_rate = (m['perfect_extractions'] / m['total_images'] * 100) if m['total_images'] > 0 else 0
        print(f"   Perfect extractions: {m['perfect_extractions']}/{m['total_images']} ({perfect_rate:.1f}%)")

        # Position detection
        print(f"\n🔢 Position Detection:")
        pos_accuracy = (m['positions_detected'] / m['positions_total'] * 100) if m['positions_total'] > 0 else 0
        print(f"   Detected: {m['positions_detected']}/{m['positions_total']} ({pos_accuracy:.1f}%)")
        print(f"   Missed: {m['positions_missed']}")
        print(f"   False positives: {m['positions_false']}")

        # Name extraction
        print(f"\n📝 Name Extraction (for detected positions):")
        name_accuracy = (m['names_exact_match'] / m['names_total'] * 100) if m['names_total'] > 0 else 0
        print(f"   Exact matches: {m['names_exact_match']}/{m['names_total']} ({name_accuracy:.1f}%)")

        if m['names_total'] > m['names_exact_match']:
            avg_edit_dist = m['names_total_edit_distance'] / (m['names_total'] - m['names_exact_match'])
            print(f"   Average edit distance (errors): {avg_edit_dist:.2f} characters")

    # Position 11 specific analysis
    print(f"\n{'─' * 80}")
    print(f"🎯 POSITION 11 DETECTION (Primary Issue)")
    print(f"{'─' * 80}")
    print(f"Test images with rank 11: {position_11_stats['total_with_11']}")

    if position_11_stats['total_with_11'] > 0:
        custom_11_rate = (position_11_stats['custom_detected'] / position_11_stats['total_with_11'] * 100)
        baseline_11_rate = (position_11_stats['baseline_detected'] / position_11_stats['total_with_11'] * 100)

        print(f"\n{model_name} detected: {position_11_stats['custom_detected']}/{position_11_stats['total_with_11']} ({custom_11_rate:.1f}%)")
        print(f"{baseline_model} detected: {position_11_stats['baseline_detected']}/{position_11_stats['total_with_11']} ({baseline_11_rate:.1f}%)")

        improvement = custom_11_rate - baseline_11_rate
        print(f"\n{'📈' if improvement > 0 else '📉'} Improvement: {improvement:+.1f}%")
    else:
        print("⚠️  No test images contain position 11")
        print("   Recommendation: Add more diverse test data with position 11")

    # Comparison
    print(f"\n{'=' * 80}")
    print(f"⚖️  CUSTOM vs BASELINE COMPARISON")
    print(f"{'=' * 80}")

    custom_pos_acc = (metrics['custom']['positions_detected'] / metrics['custom']['positions_total'] * 100) if metrics['custom']['positions_total'] > 0 else 0
    baseline_pos_acc = (metrics['baseline']['positions_detected'] / metrics['baseline']['positions_total'] * 100) if metrics['baseline']['positions_total'] > 0 else 0

    custom_name_acc = (metrics['custom']['names_exact_match'] / metrics['custom']['names_total'] * 100) if metrics['custom']['names_total'] > 0 else 0
    baseline_name_acc = (metrics['baseline']['names_exact_match'] / metrics['baseline']['names_total'] * 100) if metrics['baseline']['names_total'] > 0 else 0

    print(f"\nPosition detection: {custom_pos_acc:.1f}% vs {baseline_pos_acc:.1f}% ({custom_pos_acc - baseline_pos_acc:+.1f}%)")
    print(f"Name extraction: {custom_name_acc:.1f}% vs {baseline_name_acc:.1f}% ({custom_name_acc - baseline_name_acc:+.1f}%)")

    # Show worst errors
    print(f"\n{'=' * 80}")
    print(f"❌ TOP 5 PROBLEM CASES")
    print(f"{'=' * 80}")

    for model_type in ['custom', 'baseline']:
        model_label = f"{model_name}" if model_type == 'custom' else f"{baseline_model}"
        cases = sorted(problem_cases[model_type], key=lambda x: x['edit_distance'], reverse=True)[:5]

        if cases:
            print(f"\n{model_label}:")
            for i, case in enumerate(cases, 1):
                print(f"  {i}. {case['image']} - Rank {case['position']}")
                print(f"     Expected: '{case['expected']}'")
                print(f"     Got:      '{case['got']}'")
                print(f"     Edit distance: {case['edit_distance']}")

    # Recommendations
    print(f"\n{'=' * 80}")
    print(f"💡 RECOMMENDATIONS")
    print(f"{'=' * 80}")

    overall_improvement = custom_pos_acc - baseline_pos_acc

    if overall_improvement > 10:
        print("✅ Excellent! Custom model shows significant improvement.")
        print("   → Deploy to production")
    elif overall_improvement > 5:
        print("👍 Good! Custom model is better.")
        print("   → Consider collecting more training data for further gains")
    elif overall_improvement > 0:
        print("📊 Modest improvement.")
        print("   → Needs more diverse training data")
        print("   → Focus on problem cases in training set")
    else:
        print("⚠️  Custom model not better than baseline.")
        print("   Possible issues:")
        print("   → Training data too similar to baseline strengths")
        print("   → Ground truth annotations contain errors")
        print("   → Need more training iterations")
        print("   → Test set too small or not representative")

    if position_11_stats['total_with_11'] < 5:
        print("\n⚠️  Limited position 11 test cases!")
        print("   → Add more screenshots with rank 11 to test set")

    # Save detailed results
    results_file = Path(__file__).parent.parent / "evaluation_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'metrics': {k: dict(v) for k, v in metrics.items()},
            'position_11': position_11_stats,
            'problem_cases': problem_cases
        }, f, indent=2)

    print(f"\n📄 Detailed results saved to: {results_file}")
    print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python 05_evaluate_model.py <test_screenshots_dir> <test_ground_truth_dir> [custom_model] [baseline_model]")
        print("\nExample:")
        print("  python 05_evaluate_model.py ../screenshots_test/ ../ground_truth_test/")
        print("  python 05_evaluate_model.py ../screenshots_test/ ../ground_truth_test/ vri eng")
        sys.exit(1)

    test_screenshots = sys.argv[1]
    test_ground_truth = sys.argv[2]
    custom_model = sys.argv[3] if len(sys.argv) > 3 else "vri"
    baseline_model = sys.argv[4] if len(sys.argv) > 4 else "eng"

    evaluate_model(test_screenshots, test_ground_truth, custom_model, baseline_model)
