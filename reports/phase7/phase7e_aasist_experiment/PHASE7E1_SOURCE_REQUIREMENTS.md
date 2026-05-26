# Phase 7E1 — AASIST Source Requirements

**Status:** Active  
**Scope:** What must be provided before AASIST training or 7E3A pretrained eval

---

## FASSD scaffold is not AASIST source

The directory `code/phase7/aasist/` in this repo holds **integration tooling only** (audit, environment check, smoke test, future adapter). It is **not** the official AASIST anti-spoofing implementation.

| What | Role |
|------|------|
| `code/phase7/aasist/integration/` | FASSD scripts — **scaffold** |
| `code/phase7/aasist/vendor/AASIST/` | **Required** location for verified upstream source |
| `external/AASIST/` | Alternate location at repo root |

An `aasist.zip` (if you have one) must be **extracted** into `vendor/AASIST/` (or `external/AASIST/`). Do not assume the zip or scaffold folder satisfies source audit.

**Expected first audit verdict:** `SOURCE_REQUIRED` until vendor source is present.

---

## Acceptable source options

### Option 1 — Local vendor tree (recommended for reproducibility)

```text
code/phase7/aasist/vendor/AASIST/
```

Full upstream repository clone/copy with README, license, model definition, and training/eval scripts **as published by authors**.

### Option 2 — External folder at repo root

```text
external/AASIST/
```

Pass to scripts:

```text
--aasist_src external/AASIST
```

### Option 3 — Installed Python package (Mode B)

If a maintained package is installed in **`(fassd)`**, audit/smoke scripts attempt import detection. You must still verify:

- Version matches paper/reference implementation  
- License allows project use  
- Checkpoint compatibility for 7E3A

---

## Checkpoint (optional in 7E1, required for 7E3A)

| Phase | Checkpoint |
|-------|------------|
| **7E1** | Optional — needed only for load/forward smoke beyond import |
| **7E3A** | **Required** for pretrained evaluation (or documented impossibility) |

Place checkpoints **outside** git if large; pass `--checkpoint_path` to smoke test. Do **not** commit multi-GB weights without LFS policy.

---

## Unacceptable approaches

| Do not | Why |
|--------|-----|
| Hand-write a “similar” attention model and call it AASIST | Invalid experiment; breaks benchmark meaning |
| Copy random GitHub forks without verification | Unknown architecture/checkpoint mismatch |
| Train in 7E1 smoke scripts | Out of scope |
| Auto-download weights in 7E1 | User must approve downloads in later phase |
| Use 7C4-v2 decisions as AASIST labels | Wrong supervision |

---

## Verification checklist

- [ ] README identifies project as AASIST / anti-spoofing with clear citation  
- [ ] LICENSE file present  
- [ ] Model class discoverable (audit lists `model_candidates`)  
- [ ] Config or README states sample rate / input format  
- [ ] Smoke test: `PASS` or `PASS_IMPORT_ONLY` at minimum  
- [ ] Environment check: `PASS` with CUDA on target laptop  

---

## If source is missing (expected first run)

Scripts return **`SOURCE_REQUIRED`** with user actions. That is **OK** for 7E1 scaffolding.

Proceed to 7E2/7E3A only after source is provided and smoke test confirms import/instantiation path.

---

## Related

- [PHASE7E1_AASIST_INTEGRATION_PLAN.md](PHASE7E1_AASIST_INTEGRATION_PLAN.md)  
- [code/phase7/aasist/README.md](../../../code/phase7/aasist/README.md)
