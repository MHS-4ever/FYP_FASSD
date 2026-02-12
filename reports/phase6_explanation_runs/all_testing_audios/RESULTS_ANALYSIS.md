# Phase 6 Results: All Testing Audios (Detailed)

**Run**: `all_testing_audios`  
**Convention**: **r = real**, **f = fake** (for Trump, Pakistani, and any other files). Filenames are correct.

**Note:** These results and the full `testing_audios/` layout (pakistani, trump, synthetic_fake) are kept as-is. Further work focuses **only on Trump testing audios** (`testing_audios/trump/`).

---

## 1. Trump audios (8 files)

| File       | True label | Prediction | decision_score | n_chunks_used | Correct? |
|------------|------------|------------|-----------------|---------------|----------|
| trump_f1   | FAKE       | FAKE       | 1.000           | 47/48         | ✅       |
| trump_f2   | FAKE       | FAKE       | 1.000           | 24/24         | ✅       |
| trump_f3   | FAKE       | FAKE       | 0.944           | 36/38         | ✅       |
| trump_r1   | REAL       | REAL       | 0.156           | 475/542       | ✅       |
| trump_r2   | REAL       | REAL       | 0.676           | 1326/1610     | ✅       |
| trump_r3   | REAL       | REAL       | 0.486           | 1278/1648     | ✅       |
| trump_r4   | REAL       | REAL       | 0.220           | 522/677       | ✅       |
| trump_r5   | REAL       | REAL       | 0.535           | 523/549       | ✅       |

**Trump accuracy: 8/8 (100%)**

- All 3 fake files predicted FAKE (high decision_score, 0.94–1.0).
- All 5 real files predicted REAL (decision_score below vote_threshold 0.70; trump_r2 and r5 are close at 0.68 and 0.54 but still below 0.70).
- VAD and pct_vote are behaving as intended on this set.

---

## 2. Pakistani audios (8 files) — kept for reference

| File               | True label | Prediction | decision_score | spoof_prob_mean | spoof_prob_median | n_chunks_used | Correct? |
|--------------------|------------|------------|----------------|-----------------|-------------------|---------------|----------|
| imran_khan_f1      | FAKE       | FAKE       | 0.742          | 0.731           | 0.948             | 89/93         | ✅       |
| imran_khan_f2      | FAKE       | **REAL**   | 0.611          | 0.615           | 0.810             | 36/39         | ❌ FN    |
| imran_khan_f3      | FAKE       | FAKE       | 0.733          | 0.762           | 0.972             | 30/31         | ✅       |
| imran_khan_r2      | REAL       | **FAKE**   | 0.828          | 0.825           | 0.999             | 29/29         | ❌ FP    |
| imran_khan_r3      | REAL       | **FAKE**   | 0.941          | 0.935           | 1.000             | 34/44         | ❌ FP    |
| imran_khan_real1   | REAL       | **FAKE**   | 0.960          | 0.977           | 1.000             | 25/25         | ❌ FP    |
| saqib_nisar_f1     | FAKE       | FAKE       | 1.000          | 0.992           | 1.000             | 12/12         | ✅       |
| saqib_nisar_son_r1 | REAL       | **FAKE**   | 0.900          | 0.918           | 1.000             | 40/45         | ❌ FP    |

**Pakistani accuracy: 3/8 (37.5%)**

- **False negative (1)**: imran_khan_f2 (true FAKE, predicted REAL). decision_score 0.611 &lt; 0.70.
- **False positives (4)**: imran_khan_r2, r3, real1, saqib_nisar_son_r1 (true REAL, predicted FAKE). All have high decision_score (0.83–0.96).
- **Correct (3)**: imran_khan_f1, imran_khan_f3, saqib_nisar_f1 (all FAKE correctly detected).
- The model is biased toward FAKE on Pakistani real speech (domain shift; model trained mainly on English/ASVspoof).

---

## 3. Synthetic (1 file)

| File         | True label | Prediction | decision_score | Correct? |
|--------------|------------|------------|----------------|----------|
| synthetic_f1 | FAKE       | FAKE       | 0.900          | ✅       |

**Synthetic: 1/1 (100%)**

---

## 4. Overall summary

| Category   | Correct | Total | Accuracy   |
|-----------|---------|-------|------------|
| Trump     | 8       | 8     | **100%**   |
| Pakistani | 3       | 8     | **37.5%**  |
| Synthetic | 1       | 1     | **100%**   |
| **Total** | **12**  | **17**| **70.6%**  |

- **Trump**: All correct; naming (r=real, f=fake) and predictions align.
- **Pakistani**: Main errors are real speech predicted as FAKE (4 FP, 1 FN). Priority for improvement (e.g. Phase 7 / domain adaptation on Pakistani data).
- **Synthetic**: Correctly detected as FAKE.

---

## 5. How to read the CSV

- **decision_score** = pct_chunks_above_chunk_threshold (fraction of chunks with spoof_prob ≥ 0.65).
- **Prediction**: FAKE if decision_score ≥ **vote_threshold (0.70)**; otherwise REAL.
- **spoof_prob_mean / median**: chunk-level spoof probability (mean/median across chunks used after VAD).
- **attack_type**: multiclass (bonafide, synthesis, conversion, replay); secondary to binary real/fake.
