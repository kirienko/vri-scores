# Best Practices for OCR Model Training

## The Golden Rule: Train/Test Split

**NEVER test your model on data it was trained on!** This gives falsely optimistic results.

### Why This Matters

```
❌ Bad Practice:
- Train on 100 screenshots
- Test on the same 100 screenshots
- Report 99% accuracy
- Deploy to production
- Real-world accuracy is only 70% 😞

✅ Good Practice:
- Split 100 screenshots: 80 train, 20 test
- Train on 80 screenshots only
- Test on the 20 held-out screenshots
- Report 85% accuracy
- Deploy to production
- Real-world accuracy is 85% ✨
```

### Proper Workflow

```bash
# 1. Collect and annotate ALL your screenshots first
cd /home/user/vri-scores/training
cp /your/screenshots/*.png screenshots/
python3 scripts/batch_annotate.py screenshots/

# 2. Split into train/test BEFORE training
python3 scripts/00_split_dataset.py

# This creates:
#   screenshots_train/      ← Use for training (80%)
#   screenshots_test/       ← Use for evaluation only (20%)
#   ground_truth_train/
#   ground_truth_test/

# 3. Train on TRAINING data only
cd scripts/
./00_quick_train.sh  # Automatically uses screenshots_train/

# 4. Evaluate on TEST data (unseen during training)
python3 05_evaluate_model.py ../screenshots_test/ ../ground_truth_test/

# 5. Deploy if test accuracy is good
sudo cp ../output/vri.traineddata /usr/share/tesseract-ocr/5/tessdata/
```

## Training Data Guidelines

### Minimum Dataset Sizes

| Dataset Size | Expected Quality | Recommendation |
|-------------|------------------|----------------|
| 10-20 images | Poor | Proof of concept only |
| 50-100 images | Good | Minimum for production |
| 200-500 images | Very good | Recommended |
| 1000+ images | Excellent | Diminishing returns |

### Data Diversity Checklist

Make sure your training data includes:

- [ ] **Different ranking sizes**
  - Small races (10-15 players)
  - Medium races (20-30 players)
  - Large races (40+ players)

- [ ] **Position variety**
  - Single digits (1-9)
  - Position 10 (boundary case)
  - **Position 11 (the problem case!)**
  - Position 12-19
  - Position 20+ if applicable

- [ ] **Name diversity**
  - ASCII names (PlayerName, Cool_Guy_123)
  - Cyrillic names (Чемпион, Победитель)
  - Japanese names (水手, 船乗り)
  - Mixed (Player_日本)
  - Special characters (Player:de, Guest-123)
  - Very long names (testing edge cases)
  - Very short names (A, AB)

- [ ] **Status variety**
  - Normal finishes (1, 2, 3...)
  - DSQ (disqualified)
  - DNF (did not finish)

- [ ] **Visual variety**
  - Different times of day (if UI changes)
  - Different zoom levels
  - Different screen resolutions
  - Slightly blurry screenshots
  - High-quality screenshots

### Ground Truth Quality

Your model is only as good as your ground truth!

**Common mistakes:**
```
❌ Wrong: "11- CNS_Franconia"     (missing space after dash)
✅ Right: "11 - CNS_Franconia"

❌ Wrong: "8 - TauMeister.de"     (period instead of colon)
✅ Right: "8 - TauMeister:de"

❌ Wrong: "5 - Johannes  Bahnsen" (double space)
✅ Right: "5 - Johannes Bahnsen"
```

**Verification tips:**
- Zoom into screenshots to verify exact characters
- Copy-paste names from original game when possible
- Double-check special characters (: vs . vs ,)
- Use the batch_annotate.py script to let OCR help you

## Train/Test Split Ratios

### Standard Split: 80/20

```python
python3 00_split_dataset.py --test-ratio 0.2
```

Most common choice. Good balance of training data and test data.

### Small Dataset: 90/10

```python
python3 00_split_dataset.py --test-ratio 0.1
```

Use when you have <50 images. Maximizes training data.

### Large Dataset: 70/30 or 60/20/20

```python
# 70/30 split
python3 00_split_dataset.py --test-ratio 0.3

# For 60/20/20 (train/validation/test):
# Manually split further or modify script
```

Use when you have 500+ images. Allows for validation set too.

## Avoiding Data Leakage

### What is Data Leakage?

When test data "leaks" into training, giving false accuracy.

**Examples of leakage:**

❌ **Duplicate images**
```
screenshots/race_001.png  ← Training
screenshots/race_001_copy.png  ← Test (DUPLICATE!)
```
Result: Model memorizes the image, 100% accuracy on duplicate

❌ **Similar screenshots from same race**
```
screenshots/race_001_before.png  ← Training
screenshots/race_001_after.png   ← Test (same players, slightly different)
```
Result: Model recognizes player names, inflated accuracy

❌ **Looking at test data during training**
```
# You check test data and see position 11 fails often
# You add more position 11 examples to training
# You retrain
# Accuracy improves!
```
Result: You've indirectly used test data to improve training

### How to Prevent Leakage

✅ **Split ONCE at the beginning**
- Don't re-split after looking at results
- Use fixed random seed (--seed 42)
- Document which images are in test set

✅ **Remove duplicates before splitting**
```bash
# Check for duplicates
cd screenshots/
md5sum *.png | sort | uniq -d -w32

# Remove duplicates manually
```

✅ **Keep test set locked away**
```bash
# Only look at test set for final evaluation
# Don't peek during training!
```

✅ **Time-based split for continuous collection**
```
screenshots/2024-01-01_to_2024-06-30/  ← Training
screenshots/2024-07-01_to_2024-07-31/  ← Test
```

## Iterative Improvement Strategy

### Cycle 1: Initial Model
```
1. Collect 50-100 diverse screenshots
2. Split 80/20
3. Train quick model
4. Evaluate on test set
5. Baseline established! (e.g., 85% accuracy)
```

### Cycle 2: Improve on Failures
```
1. Deploy model to production
2. Collect screenshots where OCR fails in production
3. Annotate failures
4. Add to training set (NOT test set!)
5. Retrain with augmented training data
6. Re-evaluate on SAME test set
7. Accuracy improves to 90%
```

### Cycle 3: New Test Set
```
1. After several cycles, test set becomes stale
2. Collect NEW screenshots (recent production data)
3. Create NEW test set
4. Evaluate on new test set
5. This validates real-world performance
```

## Common Pitfalls

### Pitfall 1: Test Set Too Small
```
Total: 30 images
Train: 27 images
Test: 3 images  ❌ Too small!

Problem: 3 images not representative
Solution: Collect more data OR use 10% split (24 train, 6 test)
```

### Pitfall 2: Test Set Not Representative
```
Training set: Mix of small and large races
Test set: Only large races  ❌ Biased!

Problem: Model never trained on large races well
Solution: Ensure test set mirrors training distribution
```

### Pitfall 3: Overfitting to Training Data
```
Training accuracy: 99%
Test accuracy: 70%  ❌ Overfit!

Problem: Model memorized training data
Solution:
- More diverse training data
- Reduce training iterations
- Add regularization (if possible in Tesseract)
```

### Pitfall 4: Changing Test Set
```
Iteration 1: Test accuracy 85%
Iteration 2: Change test set, test accuracy 90%  ❌ Can't compare!

Problem: Don't know if model improved or test got easier
Solution: Keep same test set across iterations
```

## Evaluation Metrics to Track

### Use the Comprehensive Evaluation Script

```bash
python3 05_evaluate_model.py ../screenshots_test/ ../ground_truth_test/
```

This reports:

1. **Position Detection Rate**
   - Most important: Did we detect rank 11?
   - Overall: What % of positions detected?

2. **Name Extraction Accuracy**
   - Exact match rate
   - Edit distance for errors

3. **Perfect Extraction Rate**
   - What % of screenshots are 100% correct?
   - This is the real-world metric!

4. **Problem Case Analysis**
   - Which specific errors occur?
   - Where should we collect more training data?

### Track Over Time

```bash
# Save evaluation history
mkdir -p evaluation_history/

# After each training
python3 05_evaluate_model.py ../screenshots_test/ ../ground_truth_test/ > \
    ../evaluation_history/eval_$(date +%Y%m%d).txt

# Compare over time
diff evaluation_history/eval_20240601.txt evaluation_history/eval_20240615.txt
```

## Summary: The Right Way

```bash
# Phase 1: Data Collection (one time)
1. Collect diverse screenshots (50-200+)
2. Annotate with batch_annotate.py
3. Verify ground truth quality

# Phase 2: Initial Training (one time)
4. Split dataset (00_split_dataset.py)
5. Train on training set only
6. Evaluate on test set
7. Establish baseline

# Phase 3: Iterative Improvement (ongoing)
8. Deploy to production
9. Collect production failures
10. Add failures to TRAINING set
11. Retrain
12. Re-evaluate on SAME test set
13. Deploy if improved
14. Repeat

# Phase 4: Validation (monthly)
15. Create new test set from recent data
16. Evaluate on new test set
17. Verify real-world performance maintains
```

**Remember:** The goal isn't high test accuracy. The goal is high **real-world** accuracy. Proper train/test split ensures your test accuracy predicts real-world performance!
