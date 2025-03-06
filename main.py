import pytesseract
from PIL import Image
import re
import sys

# Recognize patterns from images
def extract_rankings(image_paths):
    ranking_pattern = re.compile(r'(\d+)\s?-\s?(.+)')
    rankings = {}

    for image_path in image_paths:
        img = Image.open(image_path)
        text = pytesseract.image_to_boxes(img)
        print(text)

        for line in text.split('\n'):
            match = ranking_pattern.match(line.strip())
            if match:
                rank = int(match.group(1))
                username = match.group(2).strip()
                rankings[rank] = username

    return [f"{rank} {rankings[rank]}" for rank in sorted(rankings.keys())]

# Main execution
if __name__ == "__main__":
    image_paths = sys.argv[1:]  # Pass image paths as arguments
    ordered_list = extract_rankings(image_paths)
    print("\n".join(ordered_list))