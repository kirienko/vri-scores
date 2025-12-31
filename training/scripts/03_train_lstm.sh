#!/bin/bash
# Train a custom Tesseract LSTM model for VRI rankings
# This script fine-tunes the existing English model with VRI-specific data

set -e  # Exit on error

echo "🚀 Starting Tesseract LSTM training for VRI rankings"
echo "=================================================="

# Configuration
MODEL_NAME="vri"
BASE_MODEL="eng"  # Start from English model
TRAINING_DATA_DIR="$(cd "$(dirname "$0")/../box_files" && pwd)"
OUTPUT_DIR="$(cd "$(dirname "$0")/../lstm_training" && pwd)"
FINAL_MODEL_DIR="$(cd "$(dirname "$0")/../output" && pwd)"

# Create directories
mkdir -p "$OUTPUT_DIR"
mkdir -p "$FINAL_MODEL_DIR"

echo "📁 Directories:"
echo "   Training data: $TRAINING_DATA_DIR"
echo "   Output: $OUTPUT_DIR"
echo "   Final model: $FINAL_MODEL_DIR"

# Check if training data exists
if [ ! "$(ls -A $TRAINING_DATA_DIR/*.box 2>/dev/null)" ]; then
    echo "❌ No .box files found in $TRAINING_DATA_DIR"
    echo "   Run 02_create_box_files.py first!"
    exit 1
fi

echo ""
echo "📦 Step 1: Extract base model data"
echo "----------------------------------"

# Extract the LSTM model from the base language
if [ ! -f "$OUTPUT_DIR/${BASE_MODEL}.traineddata" ]; then
    echo "Copying base model..."
    cp /usr/share/tesseract-ocr/5/tessdata/${BASE_MODEL}.traineddata "$OUTPUT_DIR/" || {
        echo "❌ Failed to find base model. Install: sudo apt-get install tesseract-ocr-${BASE_MODEL}"
        exit 1
    }
fi

# Extract LSTM network from base model
echo "Extracting LSTM network..."
combine_tessdata -e "$OUTPUT_DIR/${BASE_MODEL}.traineddata" "$OUTPUT_DIR/${BASE_MODEL}.lstm"

echo ""
echo "📝 Step 2: Create training list file"
echo "-------------------------------------"

# Create list of training files
ls "$TRAINING_DATA_DIR"/*.box | sed "s/\.box$//" > "$OUTPUT_DIR/vri.training_files.txt"
NUM_FILES=$(wc -l < "$OUTPUT_DIR/vri.training_files.txt")
echo "Found $NUM_FILES training files"

echo ""
echo "🔧 Step 3: Generate training data"
echo "----------------------------------"

# For each .box file, create .lstmf file (LSTM training format)
while IFS= read -r base_file; do
    base_name=$(basename "$base_file")
    echo "Processing: $base_name"

    tesseract "$base_file.tif" "$OUTPUT_DIR/$base_name" \
        -l ${BASE_MODEL} \
        --psm 6 \
        lstm.train
done < "$OUTPUT_DIR/vri.training_files.txt"

echo ""
echo "🧠 Step 4: Train LSTM model"
echo "---------------------------"

# Fine-tune the model
# Parameters:
#   --model_output: Output model name
#   --continue_from: Base model to fine-tune
#   --traineddata: Base traineddata file
#   --train_listfile: List of .lstmf files
#   --max_iterations: Number of training iterations (4000 is good for fine-tuning)

lstmtraining \
    --model_output "$OUTPUT_DIR/${MODEL_NAME}" \
    --continue_from "$OUTPUT_DIR/${BASE_MODEL}.lstm" \
    --traineddata "$OUTPUT_DIR/${BASE_MODEL}.traineddata" \
    --train_listfile "$OUTPUT_DIR/vri.training_files.txt" \
    --max_iterations 4000 \
    --debug_interval -1 \
    --learning_rate 0.0001

echo ""
echo "📦 Step 5: Create final traineddata file"
echo "-----------------------------------------"

# Combine LSTM network with other model components
lstmtraining \
    --stop_training \
    --continue_from "$OUTPUT_DIR/${MODEL_NAME}_checkpoint" \
    --traineddata "$OUTPUT_DIR/${BASE_MODEL}.traineddata" \
    --model_output "$FINAL_MODEL_DIR/${MODEL_NAME}.traineddata"

echo ""
echo "✨ Training complete!"
echo "===================="
echo ""
echo "📍 Trained model location: $FINAL_MODEL_DIR/${MODEL_NAME}.traineddata"
echo ""
echo "📋 Next steps:"
echo "   1. Test the model: python 04_test_model.py"
echo "   2. Copy to Tesseract directory: sudo cp $FINAL_MODEL_DIR/${MODEL_NAME}.traineddata /usr/share/tesseract-ocr/5/tessdata/"
echo "   3. Use in your code: pytesseract.image_to_string(img, lang='vri')"
echo ""
