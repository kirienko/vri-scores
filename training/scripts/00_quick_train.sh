#!/bin/bash
# Quick training pipeline - simpler alternative using text2image
# This bypasses manual box file correction by using synthetic training data

set -e

echo "🚀 VRI Tesseract Quick Training (Using text2image)"
echo "==================================================="
echo ""
echo "This method uses synthetic training data generation."
echo "It's faster but potentially less accurate than manual box annotation."
echo ""

# Configuration
MODEL_NAME="vri"
BASE_MODEL="eng"
OUTPUT_DIR="$(cd "$(dirname "$0")/../lstm_training" && pwd)"
FINAL_DIR="$(cd "$(dirname "$0")/../output" && pwd)"
GT_DIR="$(cd "$(dirname "$0")/../ground_truth" && pwd)"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$FINAL_DIR"

# Check for ground truth files
if [ ! "$(ls -A $GT_DIR/*.gt.txt 2>/dev/null)" ]; then
    echo "❌ No ground truth files found in $GT_DIR"
    echo "   Run: python 01_prepare_ground_truth.py first"
    exit 1
fi

echo "📁 Found ground truth files in $GT_DIR"
echo ""

# Step 1: Create training text file
echo "📝 Step 1: Combining ground truth data..."
cat $GT_DIR/*.gt.txt > "$OUTPUT_DIR/training_text.txt"
NUM_LINES=$(wc -l < "$OUTPUT_DIR/training_text.txt")
echo "   Collected $NUM_LINES lines of training text"

# Step 2: Generate synthetic training images using text2image
echo ""
echo "🖼️  Step 2: Generating synthetic training images..."
echo "   This may take a few minutes..."

# Use multiple fonts to improve robustness
FONTS=(
    "Arial"
    "DejaVu Sans"
    "Liberation Sans"
    "FreeSans"
)

for font in "${FONTS[@]}"; do
    echo "   Generating with font: $font"

    text2image \
        --text "$OUTPUT_DIR/training_text.txt" \
        --outputbase "$OUTPUT_DIR/vri_${font// /_}" \
        --font "$font" \
        --fonts_dir /usr/share/fonts \
        --ptsize 12 \
        --exposure 0 \
        --degrade_image 0.8 \
        || echo "⚠️  Skipped $font (not found)"
done

# Step 3: Create training file list
echo ""
echo "📋 Step 3: Creating training list..."
ls "$OUTPUT_DIR"/*.lstmf 2>/dev/null | sed 's/\.lstmf$//' > "$OUTPUT_DIR/training_list.txt" || {
    echo "❌ No .lstmf files generated. Check font availability."
    exit 1
}

NUM_FILES=$(wc -l < "$OUTPUT_DIR/training_list.txt")
echo "   Found $NUM_FILES training files"

# Step 4: Extract base model
echo ""
echo "📦 Step 4: Extracting base model..."
if [ ! -f "$OUTPUT_DIR/${BASE_MODEL}.traineddata" ]; then
    cp /usr/share/tesseract-ocr/*/tessdata/${BASE_MODEL}.traineddata "$OUTPUT_DIR/" || {
        echo "❌ Base model not found"
        exit 1
    }
fi

combine_tessdata -e "$OUTPUT_DIR/${BASE_MODEL}.traineddata" "$OUTPUT_DIR/${BASE_MODEL}.lstm"

# Step 5: Train LSTM model
echo ""
echo "🧠 Step 5: Training LSTM model..."
echo "   This will take 10-30 minutes depending on your CPU..."
echo ""

lstmtraining \
    --model_output "$OUTPUT_DIR/${MODEL_NAME}" \
    --continue_from "$OUTPUT_DIR/${BASE_MODEL}.lstm" \
    --traineddata "$OUTPUT_DIR/${BASE_MODEL}.traineddata" \
    --train_listfile "$OUTPUT_DIR/training_list.txt" \
    --max_iterations 5000 \
    --target_error_rate 0.01 \
    --debug_interval 100

# Step 6: Create final model
echo ""
echo "📦 Step 6: Creating final model..."
lstmtraining \
    --stop_training \
    --continue_from "$OUTPUT_DIR/${MODEL_NAME}_checkpoint" \
    --traineddata "$OUTPUT_DIR/${BASE_MODEL}.traineddata" \
    --model_output "$FINAL_DIR/${MODEL_NAME}.traineddata"

echo ""
echo "✨ Training complete!"
echo "===================="
echo ""
echo "📍 Model location: $FINAL_DIR/${MODEL_NAME}.traineddata"
echo ""
echo "🔧 Installation:"
echo "   sudo cp $FINAL_DIR/${MODEL_NAME}.traineddata /usr/share/tesseract-ocr/*/tessdata/"
echo ""
echo "📝 Usage in code:"
echo "   pytesseract.image_to_string(image, lang='vri')"
echo ""
echo "🧪 Test the model:"
echo "   python scripts/04_test_model.py"
echo ""
