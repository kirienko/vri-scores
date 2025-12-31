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

### Step 3: Generate Training Data
Use the provided scripts to convert screenshots + ground truth into Tesseract training format.

### Step 4: Train the Model
Fine-tune the existing English model with your VRI-specific data.

### Step 5: Test and Deploy
Validate accuracy and integrate into the bot.

## Quick Start

See `scripts/train.sh` for the automated training pipeline.

## Expected Results

- **Before**: ~70-80% accuracy on VRI screenshots
- **After**: ~95-99% accuracy on VRI screenshots
- **Specific improvement**: "11" detection from ~30% to ~95%
