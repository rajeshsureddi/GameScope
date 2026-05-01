# MTurk template (GamingVQA)

Scripts and HTML templates for Amazon MTurk batches and the GamingVQA crowdsourcing study. This branch keeps **only** MTurk-related assets; the dataset website lives on branch `main`.

## Layout

- `create_hit_batches.py` — groups originals and distortions into batch CSVs under `create_hit_batches_non_overlap/` (and related output).
- `create_hit_batches_batchsize78/` — batch-size-78 variant outputs.
- `gen_amt_code.py` — renders AMT HTML from `amt/template.htm` using the CSV inputs below.
- `amt/` — MTurk template markup, JS, and intros.
- `parsing_codes_and_results/` — parsing and analysis utilities for study exports.
- Sample inputs: `train_vids.csv`, `sample_vids.csv`, `gold_vids.csv`, `backup_test.csv`.

## Prerequisites

- Python 3.9+
- `pip install pandas jinja2`

## 1) Generate HIT batch CSVs

```bash
python3 create_hit_batches.py
```

Edit the constants at the top of `create_hit_batches.py` if your video roots or batch size change:

- `ORIGINAL_DIR`, `DISTORTED_DIR`, `BATCH_SIZE`, `OUTPUT_DIR`, `PREFIX`

Outputs include `create_hit_batches_non_overlap/grouped_original_distorted.csv`, `batch_*.csv`, and `batch_statistics.csv`.

## 2) Render MTurk HTML

```bash
python3 gen_amt_code.py \
  --env sandbox \
  --use_github \
  --train_csv train_vids.csv \
  --sample_csv sample_vids.csv \
  --gold_csv gold_vids.csv \
  --hit_csv create_hit_batches_non_overlap/batch_1.csv \
  --backup_csv backup_test.csv \
  --hit_id 0
```

By default this writes `sandbox_rendered.htm` in the repo root (override with `--out_file`). Environment `--env`: `local` | `sandbox` | `lab_sandbox` | `amt`.

## 3) Validate

- Use `debug.html` and the rendered `*_rendered.htm` in a browser before publishing.
- Prefer MTurk **Sandbox** for end-to-end checks.

## Naming note

Directories and scripts no longer include the `rajesh_` prefix; paths inside this branch are rooted at `./` wherever the legacy tree pointed at this template folder.
