import pandas as pd
import re
import unicodedata


def clean_text(text):
    if not isinstance(text, str):
        return ""
    # Normalize unicode (case-folding/standardization)
    text = unicodedata.normalize("NFKC", text)
    # Lowercase and strip whitespace
    text = text.lower().strip()
    return text


def is_junk(text):
    if not text:
        return True
    # Minimal length
    if len(text) < 2:
        return True
    # Too many special characters (likely junk)
    special_chars = len(re.findall(r"[^a-zA-Z0-9\s]", text))
    if special_chars / len(text) > 0.5:
        return True
    return False


def clean_csv(input_path, output_path):
    print(f"Reading {input_path}...")
    df = pd.read_csv(input_path)
    original_len = len(df)

    # 1. Normalize Text and Locale
    # Normalize 'query' and 'locale' columns
    if "query" in df.columns:
        df["clean_query"] = df["query"].apply(clean_text)

    if "locale" in df.columns:
        df["locale"] = df["locale"].str.lower().str.strip().str.replace("_", "-")

    # 2. Remove Junk/Unsafe
    # Filter out junk based on query
    if "clean_query" in df.columns:
        df = df[~df["clean_query"].apply(is_junk)]

    # 3. Deduplicate exact and near-duplicates
    # Using 'clean_query' and 'locale' as the key for near-deduplication
    columns_to_dedupe = []
    if "clean_query" in df.columns:
        columns_to_dedupe.append("clean_query")
    if "locale" in df.columns:
        columns_to_dedupe.append("locale")

    if columns_to_dedupe:
        df = df.drop_duplicates(subset=columns_to_dedupe, keep="first")
        # Also dedupe by original columns if clean_query doesn't catch everything (unlikely)
        df = df.drop_duplicates(
            subset=[
                "query" if "query" in df.columns else None,
                "product_title" if "product_title" in df.columns else None,
            ],
            keep="first",
        )

    # Remove the temporary 'clean_query' column if it was just for deduping
    # Actually, the user might want the cleaned text, but let's keep the original column names
    # and just overwrite 'query' if they requested normalization.
    if "clean_query" in df.columns:
        df["query"] = df["clean_query"]
        df.drop(columns=["clean_query"], inplace=True)

    # Drop rows with all NaN
    df = df.dropna(how="all")

    final_len = len(df)
    print(f"Original Row Count: {original_len}")
    print(f"Cleaned Row Count: {final_len}")
    print(f"Removed {original_len - final_len} rows.")

    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    input_file = r"C:\Users\SOLEKTA\Desktop\Intern\Month3\Proj\geo_seo_scoring\Data\Processed\sample.csv"
    output_file = r"C:\Users\SOLEKTA\Desktop\Intern\Month3\Proj\geo_seo_scoring\Data\Processed\sample_cleaned.csv"
    clean_csv(input_file, output_file)
