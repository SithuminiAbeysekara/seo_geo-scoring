import os
import pandas as pd
import json
from groq import Groq
from dotenv import load_dotenv
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)

# Paths
BASE_PATH = r"C:\Users\SOLEKTA\Desktop\Intern\Month3\Proj\geo_seo_scoring"
RAW_DATA_PATH = os.path.join(BASE_PATH, "Data", "raw")
PROCESSED_PATH = os.path.join(BASE_PATH, "Data", "Processed")
PROCEED_PATH = os.path.join(BASE_PATH, "Proceed")
ENV_PATH = os.path.join(BASE_PATH, ".env")

# 1. Initialize API
load_dotenv(ENV_PATH)
api_key = os.getenv("GORQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

ALLOWED_INTENTS = ["informational", "commercial", "transactional", "local"]


# Robust retrying logic
@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=2, min=5, max=120),
    stop=stop_after_attempt(10),
)
def translate_query(query, language):
    if language == "us":
        return query
    prompt = f"Translate the search query to English. Return ONLY the translation.\nQuery: '{query}'"
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return completion.choices[0].message.content.strip().strip("'").strip('"')


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=2, min=5, max=120),
    stop=stop_after_attempt(10),
)
def identify_intent(query):
    system_prompt = f"""
    You are an SEO intent classifier. Classify the search query into EXACTLY ONE of these categories:
    - TRANSACTIONAL: High intent to purchase.
    - COMMERCIAL: Researching or comparing products.
    - INFORMATIONAL: Looking for information or answers.
    - LOCAL: Searching for nearby services or locations.
    
    Choose ONLY the most suitable category: {ALLOWED_INTENTS}
    Return ONLY a JSON object: {{"intent": "result"}}
    """
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: '{query}'"},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    result = json.loads(completion.choices[0].message.content)
    intent = str(result.get("intent", "INFORMATIONAL")).lower().strip()
    if intent not in ALLOWED_INTENTS:
        intent = "informational"
    return intent


def run_pipeline():
    # Cleanup Proceed folder
    if os.path.exists(PROCEED_PATH):
        for file in os.listdir(PROCEED_PATH):
            if file.endswith(".csv"):
                os.remove(os.path.join(PROCEED_PATH, file))

    output_file = os.path.join(PROCESSED_PATH, "sample.csv")

    # Merge and initialize pool (always 10000 rows limit for safety)
    print("Loading raw datasets and merging...")
    df_ex = pd.read_csv(
        os.path.join(RAW_DATA_PATH, "shopping_queries_dataset_examples.csv"),
        nrows=10000,
    )
    df_pr = pd.read_csv(
        os.path.join(RAW_DATA_PATH, "shopping_queries_dataset_products.csv")
    )
    df_merged = pd.merge(df_ex, df_pr, on="product_id", how="left")

    loc_col = (
        "product_locale_x"
        if "product_locale_x" in df_merged.columns
        else "product_locale"
    )
    df_merged["country"] = df_merged[loc_col]
    df_merged["language"] = df_merged[loc_col]

    final_cols = [
        "query",
        "esci_label",
        "product_title",
        "product_description",
        "product_brand",
        "query_id",
        "product_id",
        "intent",
        "country",
        "city",
        "language",
    ]
    for col in ["intent", "city"]:
        if col not in df_merged.columns:
            df_merged[col] = ""

    df_final = df_merged[final_cols].head(500).copy()

    # Resume logic: merge in existing progress from sample.csv
    if os.path.exists(output_file):
        print("Resuming: Loading existing progress...")
        df_old = pd.read_csv(output_file)
        df_old_small = df_old[
            ["query_id", "product_id", "query", "intent", "language"]
        ].rename(
            columns={
                "query": "old_query",
                "intent": "old_intent",
                "language": "old_language",
            }
        )
        df_final = pd.merge(
            df_final, df_old_small, on=["query_id", "product_id"], how="left"
        )

        # Keep old results where available
        df_final["intent"] = df_final["old_intent"].fillna(df_final["intent"])
        df_final["query"] = df_final["old_query"].fillna(df_final["query"])
        df_final["language"] = df_final["old_language"].fillna(df_final["language"])
        df_final.drop(columns=["old_query", "old_intent", "old_language"], inplace=True)
        print(
            f"Resumed with {df_final['intent'].apply(lambda x: str(x).strip() != '').sum()} labelled intents."
        )

    # Processing Loop
    if client:
        print("Processing 500 rows (Translation + Intent Identification)...")
        for idx, row in df_final.iterrows():
            if pd.notna(row["intent"]) and str(row["intent"]).strip() != "":
                continue

            # Translation if non-US
            if row["language"] != "us" and "en" not in str(row["language"]):
                df_final.at[idx, "query"] = translate_query(
                    row["query"], row["language"]
                )
                df_final.at[idx, "language"] = "en"

            # Intent (Strict single category)
            df_final.at[idx, "intent"] = identify_intent(df_final.at[idx, "query"])

            if (idx + 1) % 10 == 0:
                print(f"  --> Processed {idx + 1}/500 rows...")
            if (idx + 1) % 50 == 0:
                df_final.to_csv(output_file, index=False)
                print("      [Checkpoint] Progress saved.")

    df_final.to_csv(output_file, index=False)
    print(f"SUCCESS: Processed data saved at {output_file}")


if __name__ == "__main__":
    run_pipeline()
