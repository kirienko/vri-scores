# Training Workflow - Visual Guide

## Complete Pipeline with Train/Test Split

```
┌─────────────────────────────────────────────────────────────────────┐
│                     1. DATA COLLECTION                              │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    Collect many screenshots
              (50-500+ VRI ranking screenshots)
                                  │
                                  ▼
                      ┌───────────────────────┐
                      │    screenshots/       │
                      │  (all your images)    │
                      └───────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────┐
│                     2. ANNOTATION                                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
             python3 batch_annotate.py screenshots/
        (OCR helps you - just correct mistakes!)
                                  │
                                  ▼
                      ┌───────────────────────┐
                      │   ground_truth/       │
                      │  (.gt.txt files)      │
                      └───────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────┐
│              3. TRAIN/TEST SPLIT ⚠️ CRITICAL!                       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
            python3 00_split_dataset.py --test-ratio 0.2
                 (Split ONCE, maintain throughout)
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
        ┌────────────────────┐    ┌────────────────────┐
        │ screenshots_train/ │    │ screenshots_test/  │
        │ ground_truth_train/│    │ ground_truth_test/ │
        │                    │    │                    │
        │   80% of data      │    │   20% of data      │
        │  FOR TRAINING      │    │  HELD OUT FOR      │
        │      ONLY          │    │  EVALUATION ONLY   │
        └────────────────────┘    └────────────────────┘
                     │                         │
                     │                    [LOCKED AWAY]
                     │                  DON'T PEEK AT
                     │                    TEST DATA!
                     │
┌─────────────────────────────────────────────────────────────────────┐
│                     4. TRAINING                                     │
└─────────────────────────────────────────────────────────────────────┘
                     │
          ./00_quick_train.sh
    (Uses screenshots_train/ ONLY)
                     │
                     ▼
        ┌────────────────────────┐
        │  lstm_training/        │
        │  (training workspace)  │
        └────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │    output/             │
        │  vri.traineddata       │
        │  (custom OCR model)    │
        └────────────────────────┘
                     │
┌─────────────────────────────────────────────────────────────────────┐
│              5. EVALUATION (on unseen test data)                    │
└─────────────────────────────────────────────────────────────────────┘
                     │
                     ├──────────────────────────────────┐
                     │                                  │
                     ▼                                  ▼
     python3 05_evaluate_model.py          ┌────────────────────┐
       screenshots_test/                   │ screenshots_test/  │
       ground_truth_test/                  │ ground_truth_test/ │
                     │                     │  (UNSEEN DATA!)    │
                     │                     └────────────────────┘
                     ▼
        ┌─────────────────────────────────────────────┐
        │  📊 Comprehensive Metrics:                  │
        │  • Position detection: 92% (vs 78% base)    │
        │  • Position 11 detection: 95% (vs 30%!)     │
        │  • Name accuracy: 88%                       │
        │  • Perfect extractions: 75%                 │
        │  • Top problem cases identified             │
        └─────────────────────────────────────────────┘
                     │
                     ▼
               ┌─────────────┐
               │  Is it good? │
               └─────────────┘
                     │
           ┌─────────┴─────────┐
           ▼                   ▼
         YES                  NO
           │                   │
           │          ┌────────────────────┐
           │          │  Collect more data │
           │          │  Focus on failures │
           │          │  Retrain           │
           │          └────────────────────┘
           │                   │
           │                   └──────┐
           │                          │
┌──────────┴──────────────────────────┴───────────────────────────────┐
│                     6. DEPLOYMENT                                   │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
   sudo cp output/vri.traineddata /usr/share/tesseract-ocr/5/tessdata/
           │
           ▼
   Update extract.py:
   pytesseract.image_to_string(img, lang='vri')
           │
           ▼
   Deploy to production Discord bot
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│              7. MONITORING & ITERATION                              │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
   Collect screenshots where OCR fails in production
           │
           ▼
   Annotate failures → Add to screenshots_train/
   (NOT to test set!)
           │
           ▼
   Retrain with augmented training data
           │
           ▼
   Evaluate on SAME test set
   (Did we improve? 92% → 95%?)
           │
           ▼
   Deploy new version (vri_v2.traineddata)
           │
           └──────────────────────────────────┐
                                              │
                     Every few months:        │
                                              │
   Create NEW test set from recent production data
   Validate model still performs well
```

## Key Points

### ✅ DO:
- **Split data ONCE at the beginning** with `00_split_dataset.py`
- **Use training data only** for model training
- **Evaluate on test data** to get realistic accuracy
- **Add production failures** to training set for improvement
- **Keep same test set** across training iterations
- **Version your models** (vri_v1, vri_v2, vri_v3)

### ❌ DON'T:
- **Don't look at test data** during training
- **Don't change test set** between iterations (can't compare)
- **Don't train on all data** then test on same data (false accuracy)
- **Don't add test failures** back to test set (leakage!)
- **Don't skip the split** (most common mistake!)

## Realistic Accuracy Example

### ❌ Wrong Approach (No Split):
```
100 screenshots
└─ Train on all 100
└─ Test on same 100
└─ Report: 99% accuracy! 🎉
└─ Deploy to production
└─ Real accuracy: 72% 😞
└─ Users complain about errors
```

### ✅ Right Approach (Proper Split):
```
100 screenshots
├─ 80 for training
└─ 20 held out for testing (NEVER used in training)
   │
   └─ Train on 80
   └─ Test on 20 unseen
   └─ Report: 87% accuracy
   └─ Deploy to production
   └─ Real accuracy: 86% ✨
   └─ Matches test prediction!
```

## Time Investment

| Phase | First Time | Iteration |
|-------|-----------|-----------|
| Collection | 1-2 hours | Ongoing |
| Annotation | 1-2 hours | 30 min |
| **Split** | **2 min** | **0 min (once)** |
| Training | 10-30 min | 10-30 min |
| Evaluation | 2 min | 2 min |
| **Total** | **2-4 hours** | **40 min** |

The split step takes 2 minutes but **saves you from wasting weeks** on a model that doesn't work in production!

## Questions?

- **"Why can't I just test on training data?"**
  → Because the model memorizes training data. Test accuracy will be falsely high.

- **"What if I have very few screenshots (< 30)?"**
  → Use 90/10 split or collect more data. 20+ images minimum for meaningful test set.

- **"Can I peek at test data to see what's failing?"**
  → Only AFTER you've finished training and evaluated. Then collect similar failures for next iteration.

- **"How often should I retrain?"**
  → Monthly, or when you collect 50+ new failure cases from production.

- **"Should I ever change my test set?"**
  → Yes, every few months create a NEW test set from recent production data. But keep the old one for comparison!

See `BEST_PRACTICES.md` for detailed explanations and `TRAINING_SUMMARY.md` for step-by-step instructions.
