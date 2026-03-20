"""
Query Pipeline - Data Cleaning & Preparation
Integrates with existing data processing workflow
"""

import pandas as pd
import re
import os
from pathlib import Path

# ============================================================================
# CONFIGURATION - CHANGE THESE TO MATCH YOUR FILES
# ============================================================================

# Input: Use your labelled data from existing pipeline
INPUT_FILE = "../Data/Processed/labelling/sample_labelled.csv"

# Output: Prepared data for scoring
OUTPUT_FILE = "../Data/Processed/scoring_ready.csv"

# ============================================================================
# MAIN PIPELINE
# ============================================================================


def main():
    global INPUT_FILE, OUTPUT_FILE

    print("=" * 70)
    print("QUERY PIPELINE - DATA PREPARATION FOR SCORING")
    print("=" * 70)

    # Step 1: Load data
    print(f"\n[1/5] Loading data from:")
    print(f"        {INPUT_FILE}")

    try:
        df = pd.read_csv(INPUT_FILE)
        print(f"✓ Loaded {len(df):,} rows")
    except FileNotFoundError:
        print(f"✗ Error: File not found!")
        print(f"\nTrying alternative paths...")

        # Try alternative paths
        alternative_paths = ["Data/Processed/labelling/sample_labelled.csv"]

        df = None
        for path in alternative_paths:
            try:
                df = pd.read_csv(path)
                print(f"✓ Found file at: {path}")
                INPUT_FILE = path
                break
            except:
                continue

        if df is None:
            print(f"\n✗ Could not find input file!")
            print(f"\nPlease check that your file exists at one of:")
            for path in [INPUT_FILE] + alternative_paths:
                print(f"  - {path}")
            return

    print(f"✓ Columns found: {list(df.columns)}")

    # Step 2: Remove duplicates
    print(f"\n[2/5] Removing duplicate queries...")
    initial_count = len(df)

    # Remove exact duplicates based on query and product_id
    if "query" in df.columns and "product_id" in df.columns:
        df = df.drop_duplicates(subset=["query", "product_id"], keep="first")
    elif "query" in df.columns:
        df = df.drop_duplicates(subset=["query"], keep="first")
    else:
        df = df.drop_duplicates(keep="first")

    duplicates_removed = initial_count - len(df)
    print(f"✓ Removed {duplicates_removed:,} duplicates")
    print(f"✓ Remaining: {len(df):,} rows")

    # Step 3: Clean text fields
    print(f"\n[3/5] Cleaning text fields...")

    def clean_text(text):
        """Remove extra spaces and special characters"""
        if pd.isna(text):
            return text

        text = str(text)
        text = text.strip()
        text = re.sub(r"[#!]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    # Clean important text columns
    text_columns = ["query", "product_title", "product_description"]
    cleaned_count = 0
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)
            cleaned_count += 1
            print(f"✓ Cleaned {col}")

    if cleaned_count == 0:
        print("⚠ No standard text columns found - check column names")

    # Step 4: Standardize values
    print(f"\n[4/5] Standardizing values...")

    # Standardize ESCI labels (make uppercase)
    if "esci_label" in df.columns:
        df["esci_label"] = df["esci_label"].str.upper()
        print(f"✓ Standardized ESCI labels")
    else:
        print(f"⚠ Column 'esci_label' not found")

    # Standardize intent (make lowercase)
    if "intent" in df.columns:
        df["intent"] = df["intent"].str.lower()
        print(f"✓ Standardized intent values")
    else:
        print(f"⚠ Column 'intent' not found")

    # Standardize country codes (make lowercase)
    if "country" in df.columns:
        df["country"] = df["country"].str.lower()
        print(f"✓ Standardized country codes")

    # Step 5: Save prepared data
    print(f"\n[5/5] Saving prepared data...")

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(OUTPUT_FILE)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✓ Created directory: {output_dir}")

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✓ Saved to: {OUTPUT_FILE}")

    # Summary Report
    print("\n" + "=" * 70)
    print("PREPARATION COMPLETE!")
    print("=" * 70)
    print(f"\nInput:  {initial_count:,} rows")
    print(f"Output: {len(df):,} rows")
    print(f"Removed: {duplicates_removed:,} duplicates")

    # Data Quality Check
    print("\n" + "=" * 70)
    print("DATA QUALITY CHECK")
    print("=" * 70)

    required_columns = ["query", "esci_label", "intent", "product_title"]
    missing_cols = [col for col in required_columns if col not in df.columns]

    if missing_cols:
        print(f"\n⚠ Warning: Missing required columns: {missing_cols}")
        print(f"\nYour columns: {list(df.columns)}")
        print(f"\nThe scoring model may not work optimally.")
        print(f"Consider adding these columns or adjust the scoring model.")
    else:
        print(f"\n✓ All required columns present")

    # Calculate completeness for available columns
    available_required = [col for col in required_columns if col in df.columns]
    if available_required:
        completeness = {}
        for col in available_required:
            non_null = df[col].notna().sum()
            pct = (non_null / len(df)) * 100
            completeness[col] = pct

        print("\nColumn Completeness:")
        for col, pct in completeness.items():
            status = "✓" if pct >= 90 else "⚠"
            print(f"  {status} {col}: {pct:.1f}%")

        avg_completeness = sum(completeness.values()) / len(completeness)
        print(f"\nAverage Completeness: {avg_completeness:.1f}%")

        if avg_completeness >= 90:
            print("✓ PASS - Meets 90% threshold")
        else:
            print("⚠ REVIEW - Below 90% threshold")

    print("\n" + "=" * 70)
    print("Next step: Run 'python scoring_model_v1.py'")
    print("=" * 70)


if __name__ == "__main__":
    main()
