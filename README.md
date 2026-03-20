# GEO/SEO Query Scoring Engine v1

## Project Overview

Build a working v1 system that identifies underperforming customer queries and provides revenue-focused recommendations.

## Folder Structure

```
geo_seo_scoring/
│
├── README.md                          (this file)
├── QUICK_START.md                     (5-minute setup guide)
├── dataset_spec.md                    (Deliverable #1)
├── .env.example                       (environment template)
│
├── Data/
│   ├── raw/                          (original datasets)
│   │   ├── shopping_queries_dataset_examples.csv
│   │   ├── shopping_queries_dataset_products.csv
│   │   └── shopping_queries_dataset_sources.csv
│   │
│   └── Processed/
│       ├── sample.csv                (sample data - 500 rows)
│       ├── sampleselection.py        (reloads/merges raw data & translates)
│       ├── scoring_ready.csv         (final sanitized data for scoring)
│       │
│       ├── Cleanup/
│       │   ├── clean_csv.py          (existing cleaner)
│       │   └── sample_cleaned.csv    (cleaned output)
│       │
│       └── labelling/
│           ├── labeller.py           (Main labeller with multi-intent cleanup)
│           ├── generate_library.py   (existing generator)
│           ├── keyword_library.json  (keyword definitions)
│           └── sample_labelled.csv   (labelled output)

│
├── scripts/                          (scoring scripts)
│   ├── query_pipeline.py            (data prep for scoring)
│   ├── scoring_model_v1.py          (core scoring logic)
│   └── create_visualizations.py     (optional charts)
│
├── outputs/                          (results folder)
│   ├── recommendations.csv          (prioritized action items)
│   ├── scores_output.csv            (detailed scoring)
│   └── analysis_report_v1.md        (executive summary)
```

## Getting Started: Complete Pipeline Workflow

Follow these steps in order to process your raw data into final revenue-focused recommendations:

### Step 0: Environment Setup

Verify your installation and ensure all necessary folders exist.

```bash
python setup.py
```

_Result: Verified dependencies and created output directories._

### Step 1: Data Selection & Translation

Prepare the base sample (500 rows) with English translations for any non-US queries.

```bash
# Performs sampling, merging, and Groq-based translation
python Data/Processed/sampleselection.py
```

_Output: `Data/Processed/sample.csv`_

### Step 2: Data Cleaning

Clean the sample data for inconsistent formatting and missing values.

```bash
# From the project root
cd Data/Processed/Cleanup
python clean_csv.py
```

_Output: `Data/Processed/Cleanup/sample_cleaned.csv`_

### Step 3: Intent & Entity Labelling

Apply Rule-based and LLM-based labeling. This logic automatically **fixes any multi-intents** to maintain high quality.

```bash
# From the cleaning folder
cd ../labelling
python labeller.py
```

_Output: `Data/Processed/labelling/sample_labelled.csv`_

### Step 4: Scoring Pipeline

Run the metrics and recommendation engine from the **project root folder**.

```bash
# Return to root first
cd ../../../

# Step 4a: Prep data for scoring (deduplicate and sanitize)
python scripts/query_pipeline.py
# Result: Generates Data/Processed/scoring_ready.csv (final data for model)

# Step 4b: Run final scoring and generate reports
python scripts/scoring_model_v1.py
```

_Final Outputs: `outputs/scores_output.csv`, `outputs/recommendations.csv`, and `outputs/analysis_report_v1.md`_

## Key Deliverables Check

All final analysis and outputs will be located in the `outputs/` folder:

- `recommendations.csv`: Prioritized action items for SEO/GEO improvements.
- `scores_output.csv`: Detailed 0-100 scoring for each query.
- `analysis_report_v1.md`: Executive summary and revenue projections.
- `benchmark_100.csv`: Final 100 queries used for benchmarking.

## Configuration

## Deliverables Checklist

- [x] 1. `dataset_spec.md` - Data documentation
- [x] 2. `scripts/query_pipeline.py` - Data pipeline
- [x] 3. `scripts/scoring_model_v1.py` - Scoring model
- [ ] 4. `outputs/benchmark_100.csv` - Run script to generate
- [ ] 5. `outputs/scores_output.csv` - Run script to generate
- [ ] 6. `outputs/analysis_report_v1.md` - Run script to generate
- [ ] 7. `demo_slides_v1.pdf` - Create manually from results

## Documentation

- **QUICK_START.md** - 5-minute setup guide
- **docs/DELIVERABLES_SUMMARY.md** - Complete overview
- **docs/QUICK_REFERENCE.md** - One-page cheat sheet
- **docs/FILE_STRUCTURE.md** - Detailed workflow

## Support

If you encounter issues:

1. Check error messages
2. Verify file paths in configuration
3. Ensure required columns exist (see dataset_spec.md)
4. Review docs/ folder for troubleshooting

## Next Steps

1. Run the scoring pipeline
2. Review `outputs/analysis_report_v1.md`
3. Focus on HIGH priority recommendations
4. Create presentation slides using results

---

**Ready to start? Open QUICK_START.md for detailed instructions!**
