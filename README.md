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

- Use `debug.html` and the rendered `*_rendered.htm` in a browser before launching.
- Prefer MTurk **Sandbox** for end-to-end checks before going to production.

## 4) Upload videos to S3 (Sandbox)

All video URLs referenced in the HIT must be publicly accessible before MTurk workers can view them. Upload them to an S3 bucket with public-read ACL:

```bash
aws s3 cp videos/ s3://your-bucket/gamingvqa/ --recursive --acl public-read
```

Verify each URL is reachable in a browser (`https://your-bucket.s3.amazonaws.com/gamingvqa/filename.mp4`) before proceeding.

## 5) Publish on MTurk Requester

1. Go to [MTurk Requester Sandbox](https://requestersandbox.mturk.com) (or [production](https://requester.mturk.com) when ready).
2. Click **Create > New Project > Survey Link** (or use the rendered `.htm` directly via **New Project > Other**).
3. Paste the contents of `sandbox_rendered.htm` into the **Design Layout** editor, or upload it.
4. Under **Publish Batch**, upload one of the `batch_*.csv` files generated in step 1.  
   Each row in the CSV becomes one HIT assignment.
5. Set reward, max assignments per HIT, and time limit, then click **Publish**.

## 6) Preview as a Worker

1. Go to [MTurk Worker Sandbox](https://workersandbox.mturk.com) and sign in with a **separate** worker account (not the requester account).
2. Search for your HIT by title or requester name.
3. Accept and complete one HIT end-to-end to confirm video playback, slider interaction, and submission work correctly.
4. Check the Requester dashboard to verify the submitted answers appear under **Manage > Results**.
