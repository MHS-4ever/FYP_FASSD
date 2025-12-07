# Phase 7: Domain Adaptation (If Needed)

**Status**: ⏳ PENDING (OPTIONAL)  
**Priority**: 🟡 CONDITIONAL  
**Duration**: Week 5  
**Dependencies**: Phase 5 (Evaluation) - Only if Real-world EER > 20%

---

## 🎯 Objective

Fine-tune the hybrid model on additional real-world data if cross-domain performance is below target (Real-world EER > 20%).

---

## ⚠️ Trigger Condition

**This phase is ONLY needed if:**
- Real-world EER > 20% after Phase 5 evaluation
- Significant performance gap between ASVspoof and Real-world domains
- Model fails to generalize to real-world audio

**If Real-world EER < 20%:** Skip this phase and proceed to deployment/testing.

---

## 📋 Tasks

### 1. Collect Additional Real-World Data

**If Performance is Poor:**
- Identify which domains are failing (broadcast/phone/podcast/social)
- Collect additional samples from failing domains
- Minimum: 1,000+ samples per failing domain
- Focus on diverse recording conditions

**Data Collection:**
- Same process as Phase 0
- Target failing domains specifically
- Ensure quality and proper labeling

### 2. Fine-Tuning Strategy

**Option 1: Full Fine-Tuning**
- Train entire model on real-world data
- Lower learning rate (1e-4 or 1e-5)
- Fewer epochs (5-10)
- Monitor for overfitting

**Option 2: Transfer Learning**
- Freeze ResNet branch (keep spectrogram knowledge)
- Freeze Environmental branch (keep environmental knowledge)
- Train only fusion layer and output heads
- Faster training, less risk of catastrophic forgetting

**Option 3: Progressive Unfreezing**
- Start with frozen branches
- Gradually unfreeze layers
- Fine-tune progressively

**Recommended:** Option 2 (Transfer Learning) - safer, faster

### 3. Fine-Tuning Process

**Data Preparation:**
- Combine original training data + new real-world data
- Maintain 50/50 ASVspoof/Real-world mix (or adjust)
- Use speaker-independent splits

**Training Configuration:**
- Learning rate: 1e-4 (lower than initial training)
- Epochs: 5-10 (fewer than initial training)
- Batch size: 128 (same)
- Monitor: Real-world validation EER (key metric)

**Loss Weights:**
- May adjust binary/multiclass weights
- Focus on binary task (real/fake) if multiclass is less important

### 4. Evaluation After Fine-Tuning

**Compare:**
- Before fine-tuning: Real-world EER
- After fine-tuning: Real-world EER
- Improvement: Target > 5% EER reduction

**Metrics:**
- Real-world EER (should be < 20%)
- ASVspoof EER (should not degrade significantly)
- Overall EER
- Per-domain breakdown

---

## 📁 Output Files

```
models_saved/
└── hybrid_resnet_environmental_finetuned.pth    # Fine-tuned model

reports/
├── logs/
│   └── finetuning_metrics.csv                   # Fine-tuning metrics
└── evaluation/
    └── finetuned_evaluation_report.md           # Post-finetuning evaluation
```

---

## 🔧 Scripts Needed

### To Create:
- `Code/finetune_on_realworld.py` - Fine-tuning script
- `Code/compare_before_after.py` - Before/after comparison

### Existing (Reuse):
- ✅ `Code/train_hybrid_model.py` - Base training code
- ✅ `Code/evaluate_hybrid_model.py` - Evaluation code

---

## ✅ Success Criteria

- [ ] Additional real-world data collected (if needed)
- [ ] Fine-tuning completed without catastrophic forgetting
- [ ] Real-world EER < 20% (target met)
- [ ] ASVspoof performance maintained (no significant degradation)
- [ ] Improvement documented (before/after comparison)
- [ ] Fine-tuned model saved

---

## 📊 Expected Improvement

**Target:**
```
Metric                    | Before | After  | Improvement
--------------------------|--------|--------|------------
Real-world EER            | > 20%  | < 20%  | > 5% reduction
ASVspoof EER              | < 5%   | < 6%   | < 1% degradation
Overall EER                | > 10%  | < 10%  | Improvement
```

**Minimum Acceptable:**
- Real-world EER reduction: > 3%
- ASVspoof EER increase: < 2%

---

## ⚠️ Challenges & Solutions

### Challenge 1: Catastrophic Forgetting
**Problem**: Fine-tuning may forget ASVspoof knowledge  
**Solution**: 
- Use transfer learning (freeze branches)
- Mix ASVspoof + Real-world data
- Monitor ASVspoof performance

### Challenge 2: Overfitting
**Problem**: Model may overfit to new real-world data  
**Solution**: 
- Lower learning rate
- Fewer epochs
- Early stopping
- Regularization (dropout, weight decay)

### Challenge 3: Limited Data
**Problem**: Not enough real-world data for fine-tuning  
**Solution**: 
- Collect more data (Phase 0 again)
- Use data augmentation
- Consider semi-supervised learning

---

## 🔗 Dependencies

**Prerequisites:**
- ✅ Phase 5: Evaluation (need to identify poor performance)
- ✅ Trained hybrid model

**Next Phase:**
- Phase 6: Explanation System (if fine-tuning succeeds)
- Or: Re-evaluate and iterate

---

## 📝 Notes

- This phase is **OPTIONAL** - only if needed
- Don't proceed if Real-world EER already < 20%
- Monitor ASVspoof performance to avoid degradation
- Document fine-tuning process and results
- Consider multiple fine-tuning strategies if first attempt fails

---

## 🔍 Fine-Tuning Checklist

- [ ] Poor performance identified (Real-world EER > 20%)
- [ ] Additional data collected (if needed)
- [ ] Fine-tuning strategy chosen
- [ ] Fine-tuning completed
- [ ] Real-world EER improved (< 20%)
- [ ] ASVspoof performance maintained
- [ ] Before/after comparison documented
- [ ] Fine-tuned model saved

---

**Last Updated**: [Date]  
**Status**: ⏳ PENDING (CONDITIONAL)

