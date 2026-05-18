# Cursor Workflow Guide for FASSD

**Purpose:** Use Cursor efficiently without wasting tokens on this project.

---

## Goal

Use Cursor for **targeted** script and documentation work; run heavy Python jobs **locally** in the terminal; return **specific outputs** for review.

---

## Best workflow

1. Use Cursor only to **create/fix scripts** and **documentation**.  
2. Run generated Python commands **manually** in terminal (`conda activate fassd`).  
3. Send terminal summaries and **listed output files** for review.  
4. Avoid asking Cursor to “review everything again” unless needed.  
5. Keep prompts **scoped** to specific files and outputs.  
6. For big phases: **plan → implement script → run terminal → upload outputs → review → sign off**.  
7. Do **not** ask Cursor to re-read the whole repo unless necessary.

---

## Standard phase workflow

1. **Planning** — update `reports/phase7/` docs or master plan.  
2. **Script/doc implementation** — e.g. `code/phase7/*.py` only.  
3. **Manual terminal execution** — user runs commands; pastes summary.  
4. **Upload/paste required outputs** — CSVs, markdown reports listed in the prompt.  
5. **Review** — sign off phase; update docs.  
6. **Small cleanup** — doc-only fixes if needed.  
7. **Sign off** — mark phase in `PHASE7_MASTER_PLAN.md` and `NEXT_ACTIONS.md`.

---

## Prompt style

**Good:**

```text
Update only code/phase7/audit_current_training_dataset.py and regenerate these reports.
Files to send back for review: [list].
Do not train models.
```

**Avoid:**

```text
Deeply analyze everything and fix the whole project.
```

---

## Files-to-review rule

Every Cursor task should end with:

**“Files to send back for review”** — a short numbered list of paths (CSVs, markdown, code) the reviewer needs.

---

## Phase 7 reference (current)

| Phase | Status |
|-------|--------|
| 7A | Signed off |
| 7B | Signed off |
| 7C0 | Signed off |
| **7C1** | **Active** — collection plan |
| 7C | Blocked until 7C1 data validated |

See [NEXT_ACTIONS.md](NEXT_ACTIONS.md).
