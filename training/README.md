# Custom Tesseract Training for VRI Rankings

This directory contains tools and data for training a custom Tesseract OCR model optimized for Virtual Regatta Inshore ranking screenshots.

## Directory Structure

```
training/
├── screenshots/          # Original screenshots (your training images)
├── ground_truth/        # Text files with correct OCR output
├── box_files/           # Tesseract box files (auto-generated)
├── lstm_training/       # LSTM training files
├── output/              # Trained model output
└── scripts/             # Helper scripts
```

## Prerequisites

Install required tools:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev
sudo apt-get install -y tesseract-ocr-eng tesseract-ocr-rus tesseract-ocr-jpn
```

## Training Process Overview

### Step 1: Prepare Screenshots (DONE ✓)
You already have screenshots collected!

### Step 2: Create Ground Truth
For each screenshot, create a matching `.gt.txt` file with the correct text.

Example:
- `screenshot001.png` → `screenshot001.gt.txt`

Content of `screenshot001.gt.txt`:
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

### Step 3: Split Into Train/Test Sets ⚠️ CRITICAL
Split your data to get realistic accuracy metrics.

```bash
python3 scripts/00_split_dataset.py
```

Creates training (80%) and test (20%) sets. See `BEST_PRACTICES.md` for why this matters!

### Step 4: Generate Training Data
Use the provided scripts to convert screenshots + ground truth into Tesseract training format.

### Step 5: Train the Model
Fine-tune the existing English model with your VRI-specific data (uses training set only).

### Step 6: Evaluate on Test Set
Test on unseen data to get realistic accuracy predictions.

### Step 7: Deploy
Integrate validated model into the bot.

## Quick Start

```bash
# 1. Annotate your screenshots
python3 scripts/batch_annotate.py screenshots/

# 2. Split dataset (train/test)
python3 scripts/00_split_dataset.py

# 3. Train model
cd scripts/
./00_quick_train.sh

# 4. Evaluate on test set
python3 05_evaluate_model.py ../screenshots_test/ ../ground_truth_test/

# 5. Deploy if good
sudo cp ../output/vri.traineddata /usr/share/tesseract-ocr/5/tessdata/
```

See `TRAINING_SUMMARY.md` for complete guide and `BEST_PRACTICES.md` for train/test split details.

## Expected Results

- **Before**: ~70-80% accuracy on VRI screenshots
- **After**: ~95-99% accuracy on VRI screenshots
- **Specific improvement**: "11" detection from ~30% to ~95%
