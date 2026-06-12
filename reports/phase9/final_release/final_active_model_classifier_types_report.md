# Final Active Model Classifier Types Report

Generated: 2026-06-09

Scope: final Phase 8/9 active release evidence models loaded by `release/src/model_loader.py` and called by `release/src/inference_pipeline.py`.

## Active Model Classifier Table

| Active model | Saved artifact | Exact classifier type | Library | Feature set | Training script | Dataset/manifest | Rows/files/segments | Threshold | Evidence source |
|---|---|---|---|---|---|---|---:|---:|---|
| `origin_file_model` | `release/models/origin/origin_file_model__ssl__experimental.joblib` | Artifact object: `sklearn.pipeline.Pipeline`; final step `clf`: `sklearn.linear_model._logistic.LogisticRegression` (`penalty='l2'`, `class_weight='balanced'`, `solver='liblinear'`, `max_iter=2000`, `random_state=42`). Pipeline steps: `SimpleImputer`, `VarianceThreshold`, `StandardScaler`, `SelectKBest`, `LogisticRegression`. | `sklearn` / scikit-learn | File-level SSL embeddings (`ssl_emb_*`, WavLM 768-d input; `SelectKBest` selected 50). | Release artifact created by `code/phase9/release/package_phase9b_release_models.py`; original Phase 8E-1 training/evaluation script `code/phase8/models/train_phase8e1_file_level_models.py`. | `reports/phase8/models/phase8e0/phase8e0_origin_file_dataset.csv`; `reports/phase8/models/phase8e1/phase8e1_training_manifest.csv` | 46 files/rows | 0.20 | `release/config/model_paths.yaml` L1; `release/src/model_loader.py` L15-L18, L180-L188; `release/models/origin/origin_file_model__ssl__metadata.json` L3-L11, L64-L83; `release/models/origin/origin_file_model__ssl__model_card.md` L3-L8; `code/phase9/release/package_phase9b_release_models.py` L111-L142, L244-L304; `code/phase9/release/phase9b_packaging_utils.py` L235-L255; joblib inspection confirmed `type(model)=sklearn.pipeline.Pipeline`, final `clf=LogisticRegression`, `feature_names_in_count=768`, selector support=50. |
| `replay_file_model` | `release/models/replay/replay_file_model__acoustic__experimental.joblib` | Artifact object: `sklearn.pipeline.Pipeline`; final step `clf`: `sklearn.linear_model._logistic.LogisticRegression` (`penalty='l2'`, `class_weight='balanced'`, `solver='liblinear'`, `max_iter=2000`, `random_state=42`). Pipeline steps: `SimpleImputer`, `VarianceThreshold`, `StandardScaler`, `SelectKBest`, `LogisticRegression`. | `sklearn` / scikit-learn | File-level acoustic features; 59 fit-time usable acoustic features; `SelectKBest` selected 50. | Release artifact created by `code/phase9/release/package_phase9b_release_models.py`; original Phase 8E-1 training/evaluation script `code/phase8/models/train_phase8e1_file_level_models.py`. | `reports/phase8/models/phase8e0/phase8e0_replay_file_dataset.csv`; `reports/phase8/models/phase8e1/phase8e1_training_manifest.csv` | 92 files/rows | 0.65 | `release/config/model_paths.yaml` L2; `release/src/model_loader.py` L15-L18, L180-L188; `release/models/replay/replay_file_model__acoustic__metadata.json` L3-L11, L64-L85; `release/models/replay/replay_file_model__acoustic__model_card.md` L3-L8; `code/phase9/release/package_phase9b_release_models.py` L111-L142, L244-L304; `code/phase9/release/phase9b_packaging_utils.py` L235-L255; joblib inspection confirmed `type(model)=sklearn.pipeline.Pipeline`, final `clf=LogisticRegression`, `feature_names_in_count=59`, selector support=50. |
| `mixer_file_model` | `release/models/mixer/mixer_file_model__acoustic__experimental.joblib` | Artifact object: `sklearn.pipeline.Pipeline`; final step `clf`: `sklearn.linear_model._logistic.LogisticRegression` (`penalty='l2'`, `class_weight='balanced'`, `solver='liblinear'`, `max_iter=2000`, `random_state=42`). Pipeline steps: `SimpleImputer`, `VarianceThreshold`, `StandardScaler`, `SelectKBest`, `LogisticRegression`. | `sklearn` / scikit-learn | File-level acoustic features; 59 fit-time usable acoustic features; `SelectKBest` selected 50. | Release artifact created by `code/phase9/release/package_phase9b_release_models.py`; original Phase 8E-1 training/evaluation script `code/phase8/models/train_phase8e1_file_level_models.py`. | `reports/phase8/models/phase8e0/phase8e0_mixer_file_dataset.csv`; `reports/phase8/models/phase8e1/phase8e1_training_manifest.csv` | 92 files/rows | 0.75 | `release/config/model_paths.yaml` L3; `release/src/model_loader.py` L15-L18, L180-L188; `release/models/mixer/mixer_file_model__acoustic__metadata.json` L3-L11, L64-L85; `release/models/mixer/mixer_file_model__acoustic__model_card.md` L3-L8; `code/phase9/release/package_phase9b_release_models.py` L111-L142, L244-L304; `code/phase9/release/phase9b_packaging_utils.py` L235-L255; joblib inspection confirmed `type(model)=sklearn.pipeline.Pipeline`, final `clf=LogisticRegression`, `feature_names_in_count=59`, selector support=50. |
| `partial_fabrication_segment_model` | `release/models/partial_segment/partial_segment_model__combined__experimental.joblib` | Artifact object: `sklearn.pipeline.Pipeline`; final step `clf`: `sklearn.linear_model._logistic.LogisticRegression` (`penalty='l2'`, `class_weight='balanced'`, `solver='liblinear'`, `max_iter=2000`, `random_state=42`). Pipeline steps: `SimpleImputer`, `VarianceThreshold`, `StandardScaler`, `SelectKBest`, `LogisticRegression`. | `sklearn` / scikit-learn | Segment-level combined features: segment acoustic + SSL embeddings + safe localization features; 796 fit-time usable features; `SelectKBest` selected 75. | Release artifact created by `code/phase9/release/package_phase9b_release_models.py`; original Phase 8E-3 training/evaluation script `code/phase8/models/train_phase8e3_partial_segment_model.py`. | `reports/phase8/models/phase8e2/phase8e2_partial_segment_localization_table.csv`; `reports/phase8/models/phase8e2/phase8e2_inside_outside_delta_features.csv`; `reports/phase8/models/phase8e2/phase8e2_neighbor_transition_features.csv`; `reports/phase8/models/phase8e0/phase8e0_segment_level_master_dataset.csv`; `reports/phase8/models/phase8e3/phase8e3_training_manifest.csv` | 1207 trainable/packaged segments; segment master source has 4189 rows | 0.50 | `release/config/model_paths.yaml` L4; `release/src/model_loader.py` L15-L18, L180-L188; `release/src/inference_pipeline.py` L590-L592; `release/models/partial_segment/partial_segment_model__combined__metadata.json` L3-L15, L92-L140; `release/models/partial_segment/partial_segment_model__combined__model_card.md` L3-L8; `code/phase9/release/package_phase9b_release_models.py` L151-L199, L244-L304; `code/phase8/models/train_phase8e3_partial_segment_model.py` L35-L70, L250-L315; `code/phase9/release/phase9b_packaging_utils.py` L320-L396; joblib inspection confirmed `type(model)=sklearn.pipeline.Pipeline`, final `clf=LogisticRegression`, `feature_names_in_count=796`, selector support=75. |

## Deserialized Artifact Findings

The four `.joblib` files were loaded locally with the `fassd` environment Python using `joblib.load`. The exact object structure was:

- Top-level object for all four artifacts: `sklearn.pipeline.Pipeline`.
- Pipeline steps for all four artifacts: `imputer` (`sklearn.impute._base.SimpleImputer`), `variance` (`sklearn.feature_selection._variance_threshold.VarianceThreshold`), `scaler` (`sklearn.preprocessing._data.StandardScaler`), `select` (`sklearn.feature_selection._univariate_selection.SelectKBest`), `clf` (`sklearn.linear_model._logistic.LogisticRegression`).
- Final estimator parameters for all four: `C=1.0`, `penalty='l2'`, `class_weight='balanced'`, `solver='liblinear'`, `max_iter=2000`, `random_state=42`, `fit_intercept=True`, `tol=0.0001`.
- Selected feature counts from fitted selectors: origin 50, replay 50, mixer 50, partial segment 75.
- Fit-time input feature counts from fitted pipelines: origin 768, replay 59, mixer 59, partial segment 796.

These findings match the release packaging utility, which builds the final release pipeline as:

```235:255:code/phase9/release/phase9b_packaging_utils.py
def build_release_pipeline(max_selected_features: int, random_seed: int) -> Pipeline:
    if max_selected_features <= 0:
        raise ValueError("max_selected_features must be > 0")
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("variance", VarianceThreshold()),
            ("scaler", StandardScaler()),
            ("select", SelectKBest(score_func=f_classif, k=max_selected_features)),
            (
                "clf",
                LogisticRegression(
                    penalty="l2",
                    class_weight="balanced",
                    max_iter=2000,
                    solver="liblinear",
                    random_state=random_seed,
                ),
            ),
        ]
    )
```

## Active Path Notes

`release/src/model_loader.py` defines the active release keys as `("origin", "replay", "mixer", "partial_segment")` and loads those artifacts with `joblib.load`. `release/src/inference_pipeline.py` calls `origin`, `replay`, and `mixer` as file-level axes, then calls `models["partial_segment"]["model"]` for segment candidates.

`release/models/model_inventory.json` and the Phase 9F registry also document a newer `partial_fabrication_experimental_p5b` integration module and mark the legacy `partial_fabrication_segment_model` as deprecated for the P5B cascade / not active for the Phase 9E demo. That does not change the four-model Phase 9C active loader path inspected here: the requested `partial_fabrication_segment_model` artifact is still the `partial_segment` model loaded by `release/src/model_loader.py` and called by `release/src/inference_pipeline.py`.

## AASIST / ResNet / HybridResNet Status

AASIST, ResNet, and HybridResNet are not active release decision models in the four-axis release path.

Evidence:

- `release/docs/MODEL_DETAILS.md` says active models are `origin_file_model`, `replay_file_model`, `mixer_file_model`, and `partial_fabrication_segment_model`; AASIST and HybridResNet are reference-only and not used by default in live inference or fusion (`release/docs/MODEL_DETAILS.md` L46-L52).
- `release/models/reference/README_REFERENCE_MODELS.md` says AASIST and HybridResNet are legacy reference checkpoints for history/comparison only and are not part of the active fusion/inference path (`release/models/reference/README_REFERENCE_MODELS.md` L1-L19).
- `reports/phase9/integration_docs/phase9f_model_registry_guide.md` lists AASIST and HybridResNet / ResNet as `reject_for_now`, not active in fusion, and not used for voice origin, replay, mixer, or partial decisions (`reports/phase9/integration_docs/phase9f_model_registry_guide.md` L64-L80).
- `reports/phase9/final_release/phase9g_final_release_report.md` states AASIST and HybridResNet/ResNet are inactive reference models and that Phase 9G did not activate AASIST/ResNet (`reports/phase9/final_release/phase9g_final_release_report.md` L20-L28, L73-L75).

## Conclusion

The exact classifier used in the final active architecture is the same for all four requested active release models: a scikit-learn `Pipeline` ending in `sklearn.linear_model._logistic.LogisticRegression` with L2 penalty, balanced class weights, and liblinear solver.

None of the four final active release evidence models is a CNN, ResNet, HybridResNet, or AASIST model. AASIST and HybridResNet/ResNet are inactive shadow/reference/rejected models only (`reject_for_now`), not active release decision models.
