"""
Scoring Model v1 - Query Scoring System
Generates all deliverables: benchmark, scores, recommendations, report
"""

import pandas as pd
from datetime import datetime
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

# Input from query_pipeline.py
INPUT_FILE = "../Data/Processed/scoring_ready.csv"

# Outputs directory
OUTPUT_DIR = "../outputs"

# Scoring parameters
BENCHMARK_SIZE = 100
AVG_ORDER_VALUE = 50
CONVERSION_RATE = 0.02

# ============================================================================
# SCORING MODEL
# ============================================================================


class SimpleScorer:
    """Simple scoring model with 5 components"""

    def __init__(self):
        self.weights = {
            "relevance": 0.30,
            "catalog": 0.25,
            "discovery": 0.20,
            "geo": 0.15,
            "commercial": 0.10,
        }
        self.esci_values = {"E": 100, "S": 80, "C": 60, "I": 20}

    def score_relevance(self, row):
        esci = str(row.get("esci_label", "I")).upper()
        return self.esci_values.get(esci, 20)

    def score_catalog(self, row):
        score = 0
        title = str(row.get("product_title", ""))
        if title and title != "nan":
            score += min(40, len(title) / 3)

        desc = str(row.get("product_description", ""))
        if desc and desc != "nan":
            score += min(30, len(desc) / 20)

        brand = str(row.get("product_brand", ""))
        if brand and brand != "nan" and brand.lower() != "none":
            score += 15

        attrs = str(row.get("attributes", ""))
        if attrs and attrs != "nan":
            score += 15

        return min(score, 100)

    def score_discovery(self, row):
        query = str(row.get("query", "")).lower()
        title = str(row.get("product_title", "")).lower()

        if not query or not title:
            return 50

        query_words = set(query.split())
        title_words = set(title.split())

        if not query_words:
            return 50

        overlap = len(query_words & title_words) / len(query_words)
        return overlap * 100

    def score_geo(self, row):
        score = 0
        if pd.notna(row.get("country")):
            score += 40
        if pd.notna(row.get("city")):
            score += 30
        if pd.notna(row.get("language")):
            score += 30
        return min(score, 100)

    def score_commercial(self, row):
        intent = str(row.get("intent", "")).lower()
        intent_scores = {
            "transactional": 100,
            "commercial": 80,
            "local": 70,
            "informational": 40,
        }
        for key, value in intent_scores.items():
            if key in intent:
                return value
        return 50

    def score_query(self, row):
        scores = {
            "relevance": self.score_relevance(row),
            "catalog": self.score_catalog(row),
            "discovery": self.score_discovery(row),
            "geo": self.score_geo(row),
            "commercial": self.score_commercial(row),
        }

        total = sum(scores[k] * self.weights[k] for k in scores.keys())

        return {
            "overall_score": round(total, 2),
            "relevance_score": round(scores["relevance"], 2),
            "catalog_score": round(scores["catalog"], 2),
            "discovery_score": round(scores["discovery"], 2),
            "geo_score": round(scores["geo"], 2),
            "commercial_score": round(scores["commercial"], 2),
        }


# ============================================================================
# RECOMMENDATION GENERATOR
# ============================================================================


def generate_recommendations(row):
    recs = []

    if row["relevance_score"] < 50:
        recs.append(
            {
                "priority": "HIGH",
                "issue": "Poor product match",
                "action": f"Find better match for: {row['query']}",
                "impact": "+30-40 points",
            }
        )

    if row["catalog_score"] < 60:
        recs.append(
            {
                "priority": "HIGH",
                "issue": "Incomplete product data",
                "action": "Add description and attributes",
                "impact": "+15-25 points",
            }
        )

    if row["discovery_score"] < 50:
        recs.append(
            {
                "priority": "HIGH",
                "issue": "Query terms not in title",
                "action": f"Add '{row['query']}' to product title",
                "impact": "+20-30 points",
            }
        )

    if row["geo_score"] < 70:
        recs.append(
            {
                "priority": "MEDIUM",
                "issue": "Missing location data",
                "action": "Add country/city/language",
                "impact": "+15-30 points",
            }
        )

    return recs


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    print("=" * 70)
    print("SCORING MODEL v1 - GENERATING ALL DELIVERABLES")
    print("=" * 70)

    # Create output directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"\n✓ Created output directory: {OUTPUT_DIR}")

    # Step 1: Load data
    print(f"\n[1/6] Loading prepared data...")
    try:
        df = pd.read_csv(INPUT_FILE)
        print(f"✓ Loaded {len(df):,} queries from {INPUT_FILE}")
    except FileNotFoundError:
        print(f"✗ Error: {INPUT_FILE} not found!")
        print(f"\nPlease run 'python query_pipeline.py' first.")
        return

    # Step 2: Select benchmark
    print(f"\n[2/6] Selecting {BENCHMARK_SIZE} benchmark queries...")

    df["quality"] = 0
    if "query" in df.columns:
        df["quality"] += df["query"].notna().astype(int) * 25
    if "esci_label" in df.columns:
        df["quality"] += df["esci_label"].notna().astype(int) * 25
    if "intent" in df.columns:
        df["quality"] += df["intent"].notna().astype(int) * 25
    if "product_title" in df.columns:
        df["quality"] += df["product_title"].notna().astype(int) * 25

    benchmark_df = df.nlargest(BENCHMARK_SIZE, "quality").copy()
    benchmark_df = benchmark_df.drop("quality", axis=1)

    benchmark_path = os.path.join(OUTPUT_DIR, "benchmark_100.csv")
    benchmark_df.to_csv(benchmark_path, index=False)
    print(f"✓ Selected {len(benchmark_df)} queries")
    print(f"✓ Saved to: {benchmark_path}")

    # Step 3: Calculate scores
    print(f"\n[3/6] Calculating scores...")

    scorer = SimpleScorer()
    scores_list = []

    for idx, row in benchmark_df.iterrows():
        scores = scorer.score_query(row)
        scores_list.append(scores)

    scores_df = pd.DataFrame(scores_list)
    result_df = pd.concat([benchmark_df.reset_index(drop=True), scores_df], axis=1)

    scores_path = os.path.join(OUTPUT_DIR, "scores_output.csv")
    result_df.to_csv(scores_path, index=False)

    print(f"✓ Scored {len(result_df)} queries")
    print(f"  Average score: {scores_df['overall_score'].mean():.1f}/100")
    print(f"✓ Saved to: {scores_path}")

    # Step 4: Generate recommendations
    print(f"\n[4/6] Generating recommendations...")

    all_recs = []
    for idx, row in result_df.iterrows():
        recs = generate_recommendations(row)
        for rec in recs:
            rec["query"] = row["query"]
            rec["current_score"] = row["overall_score"]
            all_recs.append(rec)

    recs_df = pd.DataFrame(all_recs)

    if len(recs_df) > 0:
        priority_order = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}
        recs_df["priority_num"] = recs_df["priority"].map(priority_order)
        recs_df = recs_df.sort_values(["priority_num", "current_score"])
        recs_df = recs_df.drop("priority_num", axis=1)

        recs_path = os.path.join(OUTPUT_DIR, "recommendations.csv")
        recs_df.to_csv(recs_path, index=False)
        print(f"✓ Generated {len(recs_df)} recommendations")
        print(f"✓ Saved to: {recs_path}")
    else:
        print("✓ No recommendations - all queries score well!")
        recs_df = pd.DataFrame()

    # Step 5: Calculate revenue
    print(f"\n[5/6] Calculating revenue impact...")

    if len(recs_df) > 0:
        recs_df["affected_queries"] = recs_df["priority"].map(
            {"HIGH": 100, "MEDIUM": 50, "LOW": 20}
        )

        def parse_impact(impact_str):
            try:
                nums = impact_str.replace("+", "").replace("points", "").split("-")
                return (float(nums[0]) + float(nums[1])) / 2
            except:
                return 10

        recs_df["score_gain"] = recs_df["impact"].apply(parse_impact)

        monthly_searches = 1000
        visibility_increase = (recs_df["score_gain"] / 10) * 0.05
        additional_traffic = (
            recs_df["affected_queries"] * monthly_searches * visibility_increase
        )
        recs_df["monthly_revenue"] = (
            additional_traffic * CONVERSION_RATE * AVG_ORDER_VALUE
        )

        total_monthly = recs_df["monthly_revenue"].sum()
        total_annual = total_monthly * 12

        print(f"✓ Monthly revenue opportunity: ${total_monthly:,.2f}")
        print(f"✓ Annual revenue opportunity: ${total_annual:,.2f}")
    else:
        total_monthly = 0
        total_annual = 0

    # Step 6: Generate report
    print(f"\n[6/6] Generating analysis report...")

    report = f"""# GEO/SEO Query Scoring Analysis Report v1
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

### Dataset
- Total queries analyzed: {len(df):,}
- Benchmark queries: {len(benchmark_df)}
- Average score: {scores_df["overall_score"].mean():.1f}/100

### Score Distribution
- Excellent (75-100): {len(scores_df[scores_df["overall_score"] >= 75])}
- Good (50-75): {len(scores_df[(scores_df["overall_score"] >= 50) & (scores_df["overall_score"] < 75)])}
- Fair (25-50): {len(scores_df[(scores_df["overall_score"] >= 25) & (scores_df["overall_score"] < 50)])}
- Poor (0-25): {len(scores_df[scores_df["overall_score"] < 25])}

### Component Averages
- Relevance: {scores_df["relevance_score"].mean():.1f}/100
- Catalog: {scores_df["catalog_score"].mean():.1f}/100
- Discovery: {scores_df["discovery_score"].mean():.1f}/100
- GEO: {scores_df["geo_score"].mean():.1f}/100
- Commercial: {scores_df["commercial_score"].mean():.1f}/100

### Recommendations
- Total recommendations: {len(recs_df) if len(recs_df) > 0 else 0}
- HIGH priority: {len(recs_df[recs_df["priority"] == "HIGH"]) if len(recs_df) > 0 else 0}
- MEDIUM priority: {len(recs_df[recs_df["priority"] == "MEDIUM"]) if len(recs_df) > 0 else 0}

### Revenue Opportunity
- Estimated monthly: ${total_monthly:,.2f}
- Estimated annual: ${total_annual:,.2f}

*Assumptions: AOV=${AVG_ORDER_VALUE}, CVR={CONVERSION_RATE * 100}%, 1,000 searches/query*

## Top 10 Recommendations
"""

    if len(recs_df) > 0:
        for idx, rec in enumerate(recs_df.head(10).itertuples(), 1):
            report += f"""
{idx}. [{rec.priority}] {rec.issue}
   Query: "{rec.query}"
   Action: {rec.action}
   Impact: {rec.impact}
   Current Score: {rec.current_score:.1f}/100
"""
    else:
        report += "\nNo recommendations - all queries performing well!\n"

    report_path = os.path.join(OUTPUT_DIR, "analysis_report_v1.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✓ Saved to: {report_path}")

    # Final summary
    print("\n" + "=" * 70)
    print("✅ ALL DELIVERABLES GENERATED!")
    print("=" * 70)
    print(f"\nCheck the '{OUTPUT_DIR}' folder for:")
    print("  ✓ benchmark_100.csv")
    print("  ✓ scores_output.csv")
    print("  ✓ recommendations.csv")
    print("  ✓ analysis_report_v1.md")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
