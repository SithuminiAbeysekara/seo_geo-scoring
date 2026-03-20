"""
Visualization Script - Create Charts from Results
Optional: Run after scoring_model_v1.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

OUTPUT_DIR = '../outputs'
SCORES_FILE = os.path.join(OUTPUT_DIR, 'scores_output.csv')
RECS_FILE = os.path.join(OUTPUT_DIR, 'recommendations.csv')
CHARTS_DIR = os.path.join(OUTPUT_DIR, 'charts')

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def create_visualizations():
    print("="*70)
    print("CREATING VISUALIZATIONS")
    print("="*70)
    
    # Create charts directory
    if not os.path.exists(CHARTS_DIR):
        os.makedirs(CHARTS_DIR)
        print(f"\n✓ Created charts directory: {CHARTS_DIR}")
    
    # Load scores
    print("\n[1/3] Loading data...")
    try:
        scores_df = pd.read_csv(SCORES_FILE)
        print(f"✓ Loaded {len(scores_df)} scored queries")
    except:
        print(f"✗ Error: {SCORES_FILE} not found")
        print("Please run 'python scoring_model_v1.py' first")
        return
    
    # Create main analysis charts
    print("\n[2/3] Creating analysis charts...")
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Query Scoring Analysis', fontsize=16, fontweight='bold')
    
    # Chart 1: Score Distribution
    axes[0].hist(scores_df['overall_score'], bins=20, color='steelblue', edgecolor='black')
    axes[0].axvline(scores_df['overall_score'].mean(), color='red', linestyle='--', 
                    linewidth=2, label=f"Mean: {scores_df['overall_score'].mean():.1f}")
    axes[0].set_title('Score Distribution')
    axes[0].set_xlabel('Score (0-100)')
    axes[0].set_ylabel('Count')
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # Chart 2: Component Averages
    components = {
        'Relevance': scores_df['relevance_score'].mean(),
        'Catalog': scores_df['catalog_score'].mean(),
        'Discovery': scores_df['discovery_score'].mean(),
        'GEO': scores_df['geo_score'].mean(),
        'Commercial': scores_df['commercial_score'].mean()
    }
    
    axes[1].barh(list(components.keys()), list(components.values()), color='coral')
    axes[1].set_title('Average Component Scores')
    axes[1].set_xlabel('Score (0-100)')
    axes[1].set_xlim(0, 100)
    axes[1].grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, (k, v) in enumerate(components.items()):
        axes[1].text(v + 2, i, f'{v:.1f}', va='center')
    
    # Chart 3: Score by Intent
    if 'intent' in scores_df.columns:
        intent_avg = scores_df.groupby('intent')['overall_score'].mean().sort_values()
        axes[2].barh(intent_avg.index, intent_avg.values, color='lightgreen')
        axes[2].set_title('Average Score by Intent')
        axes[2].set_xlabel('Score (0-100)')
        axes[2].set_xlim(0, 100)
        axes[2].grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, (k, v) in enumerate(intent_avg.items()):
            axes[2].text(v + 2, i, f'{v:.1f}', va='center')
    else:
        axes[2].text(0.5, 0.5, 'Intent data\nnot available', 
                     ha='center', va='center', fontsize=12, transform=axes[2].transAxes)
        axes[2].set_title('Score by Intent')
    
    plt.tight_layout()
    
    chart_path = os.path.join(CHARTS_DIR, 'analysis_charts.png')
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved to: {chart_path}")
    plt.close()
    
    # Create recommendations chart
    print("\n[3/3] Creating recommendations chart...")
    
    try:
        recs_df = pd.read_csv(RECS_FILE)
        
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle('Recommendations Analysis', fontsize=16, fontweight='bold')
        
        # Priority distribution
        priority_counts = recs_df['priority'].value_counts()
        colors = {'HIGH': '#e74c3c', 'MEDIUM': '#f39c12', 'LOW': '#3498db'}
        bar_colors = [colors.get(p, 'gray') for p in priority_counts.index]
        
        axes[0].bar(priority_counts.index, priority_counts.values, color=bar_colors, edgecolor='black')
        axes[0].set_title('Recommendations by Priority')
        axes[0].set_ylabel('Count')
        axes[0].grid(axis='y', alpha=0.3)
        
        # Add count labels
        for i, (k, v) in enumerate(priority_counts.items()):
            axes[0].text(i, v + max(priority_counts.values)*0.02, str(v), ha='center', fontweight='bold')
        
        # Issue types
        if 'issue' in recs_df.columns:
            issue_counts = recs_df['issue'].value_counts().head(5)
            axes[1].barh(range(len(issue_counts)), issue_counts.values, color='steelblue')
            axes[1].set_yticks(range(len(issue_counts)))
            axes[1].set_yticklabels([x[:30] + '...' if len(x) > 30 else x for x in issue_counts.index])
            axes[1].set_title('Top 5 Issues')
            axes[1].set_xlabel('Count')
            axes[1].invert_yaxis()
            axes[1].grid(axis='x', alpha=0.3)
            
            # Add count labels
            for i, v in enumerate(issue_counts.values):
                axes[1].text(v + max(issue_counts.values)*0.02, i, str(v), va='center')
        
        plt.tight_layout()
        
        recs_chart_path = os.path.join(CHARTS_DIR, 'recommendations_chart.png')
        plt.savefig(recs_chart_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved to: {recs_chart_path}")
        plt.close()
        
    except:
        print("⚠ No recommendations data to visualize")
    
    # Summary
    print("\n" + "="*70)
    print("✅ VISUALIZATIONS COMPLETE!")
    print("="*70)
    print(f"\nCharts saved in: {CHARTS_DIR}/")
    print("  ✓ analysis_charts.png")
    print("  ✓ recommendations_chart.png")
    print("\n" + "="*70)

if __name__ == "__main__":
    create_visualizations()
