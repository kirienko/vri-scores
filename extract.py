import io
import re
import sys

import pytesseract
from PIL import Image, ImageFilter

def parse_rankings_from_text(text):
    """
    Parse text to extract rankings.
    Two patterns:
      1)  {number} - {name}
      2)  {number}. {flag} {name} {time/points}

    We only keep the rank and the name, ignoring flags, times, or points.
    """

    # Pattern 1: "6 - Guest_1723161531080"
    # ranking_pattern_dash = re.compile(r'(\d{1,2})\s*[-–—]\s*(.+)')
    ranking_pattern_dash = re.compile(r'.*?(\d{1,2})\s*[-–—]\s*(.+).*')

    # Pattern 2: "6. 🇫🇷 Guest_1723161531080 +00:15.2 29 pts" (or DSQ, etc.)
    # Explanation:
    #   (\d{1,2})\.\s+     => Captures rank and skips the dot
    #   (?:\S+\s+)?         => Optionally skip a single "flag" token (e.g., country code or emoji)
    #   (.*?)(?=\s+\+|\s+DSQ|$)
    #       - Capture the name (including spaces) until we see:
    #         - a space + plus sign (time)  OR
    #         - a space + DSQ              OR
    #         - end of string
    ranking_pattern_dot = re.compile(r'.*?(\d{1,2})\.\s+(?:\S+\s+)?(.*?)(?=\s+\+|\s+DSQ|$)')

    rankings = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # 1) Try dash pattern
        match_dash = ranking_pattern_dash.search(line)
        if match_dash:
            try:
                rank = int(match_dash.group(1))
                username = match_dash.group(2).strip()
                rankings[rank] = username
                continue
            except ValueError:
                pass

        # 2) Try dot pattern
        match_dot = ranking_pattern_dot.search(line)
        if match_dot:
            try:
                rank = int(match_dot.group(1))
                username = match_dot.group(2).strip()
                rankings[rank] = username
                continue
            except ValueError:
                pass

        # If neither pattern matches, ignore the line or debug-print:
        # print("No match:", line)

    return rankings

def extract_rankings_from_image(image):
    """
    Extract rankings from a PIL image.
    """
    text = pytesseract.image_to_string(image)
    return parse_rankings_from_text(text)

def extract_rankings_from_bytes(image_bytes):
    """
    Preprocess the image bytes and extract rankings.
    """
    image = preprocess_image_from_bytes(image_bytes)
    return extract_rankings_from_image(image)

def preprocess_image_from_bytes(image_bytes):
    """
    Preprocess image bytes to improve OCR accuracy.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert('L')  # Convert to grayscale
    # Simple thresholding; adjust the threshold as needed
    img = img.point(lambda x: 0 if x < 160 else 255, '1')
    img = img.filter(ImageFilter.SHARPEN)
    return img

def extract_rankings(image_paths):
    """
    Extract rankings from a list of image file paths.
    Useful for command-line usage.
    """
    combined_rankings = {}
    for image_path in image_paths:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        extracted = parse_rankings_from_text(text)
        combined_rankings.update(extracted)
    # Build a sorted list of strings
    return [f"{rank} {combined_rankings[rank]}" for rank in sorted(combined_rankings.keys())]

if __name__ == "__main__":
    image_paths = sys.argv[1:]
    ordered_list = extract_rankings(image_paths)
    print("\n".join(ordered_list))
