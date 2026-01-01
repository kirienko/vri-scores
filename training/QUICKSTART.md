# Quick Start Guide - Tesseract Training for VRI

## Prerequisites

```bash
# Install Tesseract with training tools
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev
sudo apt-get install -y tesseract-ocr-eng tesseract-ocr-rus tesseract-ocr-jpn

# Verify installation
tesseract --version  # Should show 5.x
lstmtraining --help  # Should show training options
```

## Two Training Methods

### Method 1: Quick Training (Recommended for Start) ⚡

Uses synthetic image generation. Faster but less accurate.

**Steps:**

```bash
# 1. Place your screenshots in the screenshots/ directory
mkdir -p screenshots/
cp /path/to/your/screenshots/*.png screenshots/

# 2. Create ground truth annotations
cd scripts/
python3 01_prepare_ground_truth.py ../screenshots/

# 3. Run automated training
chmod +x 00_quick_train.sh
./00_quick_train.sh

# 4. Test the model
python3 04_test_model.py ../screenshots/ ../ground_truth/
```

**Time required:** 30-60 minutes

---

### Method 2: High-Quality Training (Best Accuracy) 🎯

Uses real screenshot data with manual box corrections.

**Steps:**

```bash
# 1-2. Same as Method 1 (screenshots + ground truth)

# 3. Generate box files from real images
python3 02_create_box_files.py ../screenshots/ ../ground_truth/

# 4. MANUALLY CORRECT box files using jTessBoxEditor
# Download: https://github.com/nguyenq/jTessBoxEditor/releases
# Open each .box file and verify character positions

# 5. Train with corrected boxes
chmod +x 03_train_lstm.sh
./03_train_lstm.sh

# 6. Test the model
python3 04_test_model.py ../screenshots/ ../ground_truth/
```

**Time required:** 4-8 hours (mostly manual correction)

---

## Ground Truth Format

For each screenshot, create a `.gt.txt` file with the exact visible text.

**Example:** `screenshot001.gt.txt`

```
1 - Failed1
2 - YoKKo
3 - kisPe
4 - GER-7
5 - Johannes Bahnsen
6 - Tobias_ARV08
7 - Mats709
8 - TauMeister:de
9 - csero
10 - Sir Toby
11 - CNS_Franconia
12 - Swedesailor SWE01
13 - Dr Krull
14 - Erzpirat
```

**Important:**
- One line per ranking entry
- Match EXACT spacing and punctuation
- Include special characters (colons, underscores, etc.)
- Don't include times or points (unless training for those too)

---

## Installing the Trained Model

```bash
# Copy to Tesseract's data directory
sudo cp output/vri.traineddata /usr/share/tesseract-ocr/5/tessdata/

# Or for Docker, add to your Dockerfile:
COPY training/output/vri.traineddata /usr/share/tesseract-ocr/5/tessdata/
```

---

## Using in Your Code

```python
import pytesseract
from PIL import Image

# Before (default English)
text = pytesseract.image_to_string(image, lang='eng')

# After (custom VRI model)
text = pytesseract.image_to_string(image, lang='vri')

# Or combine both for better results
text = pytesseract.image_to_string(image, lang='vri+eng')
```

---

## Troubleshooting

### "lstmtraining: command not found"

You need Tesseract training tools:
```bash
sudo apt-get install libtesseract-dev
```

### "text2image: command not found"

Install training utilities:
```bash
sudo apt-get install tesseract-ocr-all
```

### Low accuracy after training

1. **Need more data**: Collect 50-100+ diverse screenshots
2. **Improve ground truth**: Double-check annotations for typos
3. **Box file errors** (Method 2): Carefully review box corrections
4. **Training iterations**: Try adjusting `--max_iterations` (2000-10000)

### Model not improving over base model

- Your training data may be too similar to what the base model already handles well
- Focus on **problem cases** (screenshots where base model fails)
- Ensure ground truth is 100% accurate

---

## Expected Results

| Metric | Before Training | After Training (Quick) | After Training (High-Quality) |
|--------|----------------|------------------------|------------------------------|
| Overall accuracy | 70-80% | 85-90% | 95-99% |
| "11" detection | ~30% | ~70% | ~95% |
| Multi-language names | 60-70% | 80-85% | 90-95% |
| Special characters | 50-60% | 75-80% | 85-95% |

---

## Tips for Best Results

### 1. Diverse Training Data
- Include various race sizes (10 players, 50 players, etc.)
- Different UI themes/colors
- Various name types (ASCII, Cyrillic, Japanese, with numbers/underscores)
- Different zoom levels/resolutions

### 2. Quality Over Quantity
- 50 high-quality, diverse screenshots > 200 similar ones
- Ensure perfect ground truth annotations
- Include edge cases (DSQ, DNF, long names)

### 3. Iterative Improvement
1. Train with initial dataset
2. Test on new screenshots
3. Add failures to training set
4. Retrain
5. Repeat

### 4. Combine with Code Improvements
- Training + better preprocessing = best results
- Use confidence filtering (reject low-confidence OCR)
- Implement post-OCR corrections for known issues

---

## Next Steps After Training

1. **Integrate into extract.py:**
   ```python
   text = pytesseract.image_to_string(image, lang='vri', config='--oem 3 --psm 6')
   ```

2. **Update Dockerfile:**
   ```dockerfile
   COPY training/output/vri.traineddata /usr/share/tesseract-ocr/5/tessdata/
   ```

3. **A/B Test:**
   - Run both old and new models on same images
   - Measure improvement
   - Keep statistics

4. **Continuous Improvement:**
   - Save screenshots where OCR fails
   - Periodically retrain with new failures
   - Version your models (vri_v1, vri_v2, etc.)

---

## Questions?

See full documentation: [README.md](README.md)

For Tesseract training details: https://tesseract-ocr.github.io/tessdoc/TrainingTesseract-5.html
