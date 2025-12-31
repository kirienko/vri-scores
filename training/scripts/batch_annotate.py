#!/usr/bin/env python3
"""
Batch annotation helper - OCR first, then let user correct mistakes.
Much faster than typing from scratch!
"""

import sys
from pathlib import Path
import pytesseract
from PIL import Image

# Add parent directory to path to import extract module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from extract import preprocess_image_from_bytes, parse_rankings_from_text

def auto_annotate(screenshots_dir, ground_truth_dir):
    """
    Auto-generate ground truth using current OCR, then let user correct.
    This is much faster than typing from scratch!
    """
    screenshots_dir = Path(screenshots_dir)
    ground_truth_dir = Path(ground_truth_dir)
    ground_truth_dir.mkdir(parents=True, exist_ok=True)

    image_files = sorted(screenshots_dir.glob("*.png")) + sorted(screenshots_dir.glob("*.jpg"))

    if not image_files:
        print(f"❌ No images found in {screenshots_dir}")
        return

    print(f"🤖 Auto-annotating {len(image_files)} screenshots")
    print("=" * 70)
    print("Instructions:")
    print("1. OCR will auto-generate initial text")
    print("2. Review and correct any mistakes")
    print("3. Press Enter to accept, or type 'e' to edit")
    print("=" * 70)

    for idx, img_path in enumerate(image_files, 1):
        gt_path = ground_truth_dir / f"{img_path.stem}.gt.txt"

        if gt_path.exists():
            print(f"[{idx}/{len(image_files)}] ✓ Already exists: {img_path.name}")
            continue

        print(f"\n[{idx}/{len(image_files)}] 🖼️  {img_path.name}")
        print("-" * 70)

        # Run OCR
        try:
            with open(img_path, 'rb') as f:
                image_bytes = f.read()

            # Use the same preprocessing as production
            processed_img = preprocess_image_from_bytes(image_bytes)
            text = pytesseract.image_to_string(processed_img)
            rankings = parse_rankings_from_text(text)

            # Format rankings nicely
            lines = []

            # Integer rankings first
            int_ranks = {k: v for k, v in rankings.items() if isinstance(k, int)}
            if int_ranks:
                for rank in sorted(int_ranks.keys()):
                    lines.append(f"{rank} - {int_ranks[rank]}")

            # Then string rankings (DSQ, DNF)
            str_ranks = {k: v for k, v in rankings.items() if isinstance(k, str)}
            if str_ranks:
                for rank in sorted(str_ranks.keys()):
                    lines.append(f"{rank} - {str_ranks[rank]}")

            auto_text = '\n'.join(lines)

            if not auto_text.strip():
                print("⚠️  OCR failed to extract rankings!")
                print("   Manual entry required.")
                auto_text = ""

        except Exception as e:
            print(f"⚠️  OCR error: {e}")
            auto_text = ""

        # Show auto-generated text
        if auto_text:
            print("🤖 Auto-generated text:")
            print(auto_text)
            print()

        # Prompt for correction
        print("Options:")
        print("  [Enter] - Accept as-is")
        print("  e - Edit line by line")
        print("  m - Manual entry (type all)")
        print("  s - Skip this image")
        print("  q - Quit")

        choice = input("\nYour choice: ").strip().lower()

        if choice == 'q':
            print("👋 Exiting...")
            return
        elif choice == 's':
            print("⏭️  Skipped")
            continue
        elif choice == 'm':
            print("\nEnter text manually (blank line when done):")
            lines = []
            while True:
                line = input()
                if not line.strip():
                    break
                lines.append(line)
            final_text = '\n'.join(lines)
        elif choice == 'e':
            print("\nEdit line by line (blank to keep, 'x' to delete):")
            original_lines = auto_text.split('\n')
            new_lines = []
            for i, line in enumerate(original_lines, 1):
                print(f"[{i}] {line}")
                edit = input("    ").strip()
                if edit.lower() == 'x':
                    continue  # Delete line
                elif edit == '':
                    new_lines.append(line)  # Keep original
                else:
                    new_lines.append(edit)  # Use edited version
            final_text = '\n'.join(new_lines)
        else:  # Accept as-is
            final_text = auto_text

        # Save
        if final_text.strip():
            gt_path.write_text(final_text, encoding='utf-8')
            print(f"✅ Saved: {gt_path.name}")
        else:
            print("⚠️  Empty annotation, skipped")

    print("\n✨ Batch annotation complete!")
    print(f"📁 Ground truth files saved in: {ground_truth_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_annotate.py <screenshots_dir>")
        print("Example: python batch_annotate.py ../screenshots")
        sys.exit(1)

    screenshots_dir = sys.argv[1]
    ground_truth_dir = "../ground_truth"

    auto_annotate(screenshots_dir, ground_truth_dir)
