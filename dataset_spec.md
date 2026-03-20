# Dataset Specification (Deliverable #1)

## Overview
This document defines the data structure requirements for the GEO/SEO Query Scoring Engine v1.

## Required Columns

| Column Name | Type | Required | Description | Example |
|-------------|------|----------|-------------|---------|
| `query` | Text | Yes | Customer search query | "revent 80 cfm" |
| `esci_label` | Text | Yes | Product relevance label | "E", "S", "C", or "I" |
| `product_title` | Text | Yes | Product name/title | "Panasonic FV-20VQ3..." |
| `intent` | Text | Yes | Query intent classification | "informational" |

## Optional Columns (Enhance Scoring)

| Column Name | Type | Description | Example |
|-------------|------|-------------|---------|
| `product_description` | Text | Full product description | "Panasonic whisper..." |
| `product_brand` | Text | Brand name | "Panasonic" |
| `query_id` | Text/Number | Unique query identifier | "0" |
| `product_id` | Text | Product identifier | "B000MOO21W" |
| `country` | Text | Country code | "us" |
| `city` | Text | City name | "New York" |
| `language` | Text | Language code | "en" |
| `brand` | Text | Brand extracted from query | "ReVent" |
| `category` | Text | Product category | "ventilation fans" |
| `attributes` | Text | Product attributes | "80 cfm" |
| `timestamp` | Date | Query timestamp | "2024-01-15" |
| `value_weight` | Number | Commercial value weight | 0.8 |
| `confidence` | Number | Label confidence | 0.95 |

## ESCI Label Values

ESCI (Exact, Substitute, Complement, Irrelevant) measures product-query relevance:

| Label | Meaning | Score Weight | Example |
|-------|---------|--------------|---------|
| **E** | Exact match | 1.0 (100%) | User searches "iPhone 13", product is iPhone 13 |
| **S** | Substitute | 0.8 (80%) | User searches "iPhone 13", product is iPhone 13 Pro |
| **C** | Complement | 0.6 (60%) | User searches "iPhone 13", product is iPhone 13 case |
| **I** | Irrelevant | 0.2 (20%) | User searches "iPhone 13", product is Samsung phone |

## Intent Types

Query intent classification based on user behavior:

| Intent | Description | Commercial Value | Example |
|--------|-------------|------------------|---------|
| **transactional** | Ready to purchase | High (100) | "buy iPhone 13 online" |
| **commercial** | Researching products | Medium-High (80) | "iPhone 13 vs 14" |
| **local** | Looking for local options | Medium (70) | "iPhone store near me" |
| **informational** | Seeking information | Low-Medium (40) | "how does iPhone work" |

## Data Quality Requirements

### Completeness
- **Target**: ≥90% of required columns must be filled
- **Required fields**: `query`, `esci_label`, `intent`, `product_title`
- Missing values should be empty (not "null", "NA", or "None")

### Uniqueness
- Remove exact duplicate rows
- Consider query + product_id combination for uniqueness
- Keep most recent entry if timestamps available

### Validity
- **ESCI labels**: Must be one of: E, S, C, I (case-insensitive)
- **Intent values**: Must be one of: transactional, commercial, local, informational
- **Country codes**: Use ISO 2-letter codes (us, uk, ca, etc.)
- **Language codes**: Use ISO 2-letter codes (en, es, fr, etc.)

## File Format

### CSV Structure
```csv
query,esci_label,product_title,product_description,product_brand,query_id,product_id,intent,country,language
"revent 80 cfm",I,"Panasonic FV-20VQ3 WhisperCeiling","Quiet ventilation fan...",Panasonic,0,B000MOO21W,informational,us,en
```

### Requirements
- **Format**: CSV (Comma-Separated Values)
- **Encoding**: UTF-8
- **Header**: First row must contain column names
- **Quotes**: Use quotes around text fields containing commas
- **Delimiters**: Use comma (,) as field separator
- **Line endings**: Unix (LF) or Windows (CRLF) both acceptable

## Example Rows

### Well-Formed Example
```csv
query,esci_label,product_title,intent,country,language
"wireless mouse",E,"Logitech Wireless Mouse",transactional,us,en
"laptop bags",S,"Premium Laptop Backpack",commercial,us,en
```

### Poorly-Formed Example (DO NOT USE)
```csv
query,esci_label,product_title,intent
wireless mouse,e,null,NULL
laptop bags,X,Premium Laptop Backpack,buying
```

**Issues**:
- ESCI label lowercase (should be E)
- "null" string instead of empty value
- "NULL" instead of empty value
- Invalid ESCI label "X"
- Invalid intent "buying"

## Integration with Existing Pipeline

This specification works with your existing data processing:

```
Raw Data
  ↓
Cleanup (clean_csv.py)
  ↓
Labelling (labeller.py)
  ↓
sample_labelled.csv ← Must match this spec
  ↓
Scoring Pipeline (query_pipeline.py)
  ↓
Results (scores_output.csv)
```

## Validation Checklist

Before running the scoring pipeline, verify:

- [ ] File is CSV format with UTF-8 encoding
- [ ] Header row contains correct column names
- [ ] Required columns present: query, esci_label, intent, product_title
- [ ] ESCI labels are valid: E, S, C, or I
- [ ] Intent values are valid: transactional, commercial, local, informational
- [ ] No "null", "NULL", "NA" strings (use empty values instead)
- [ ] Text with commas is properly quoted
- [ ] At least 100 rows for meaningful benchmark selection
- [ ] ≥90% completeness in required columns

## Notes

- More optional columns = better scoring accuracy
- GEO columns (country, city, language) significantly improve local SEO scoring
- Brand and category enable better segmentation analysis
- Timestamps allow trend analysis (future enhancement)

## Questions?

See `README.md` for integration details or `QUICK_START.md` for setup instructions.
