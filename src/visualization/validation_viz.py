"""
Validation Visualizations for Universal Racing Analytics.

Creates charts showing statistical validation results.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


def create_pvalue_distribution(
    validation_results: List[Dict[str, Any]],
    significance_threshold: float = 0.05,
    title: str = "P-Value Distribution",
    output_path: Path = None
) -> Path:
    """
    Create a histogram of p-values with significance threshold.
    
    Args:
        validation_results: List of validation results with 'p_value' key
        significance_threshold: Threshold for significance (default 0.05)
        title: Plot title
        output_path: Where to save the plot
        
    Returns:
        Path to the saved plot
    """
    output_path = output_path or Path("outputs/plots")
    output_path.mkdir(parents=True, exist_ok=True)
    
    p_values = [r.get("p_value", 1.0) for r in validation_results if "p_value" in r]
    
    if not p_values:
        print("[ValidationViz] No p-values to plot")
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Histogram
    n, bins, patches = ax.hist(p_values, bins=20, range=(0, 1), 
                                color='#3498db', edgecolor='white', alpha=0.7)
    
    # Color bars based on significance
    for patch, left_edge in zip(patches, bins[:-1]):
        if left_edge < significance_threshold:
            patch.set_facecolor('#2ecc71')
    
    # Threshold line
    ax.axvline(x=significance_threshold, color='#e74c3c', linestyle='--', 
               linewidth=2, label=f'Significance threshold (p={significance_threshold})')
    
    # Labels
    ax.set_xlabel("P-Value")
    ax.set_ylabel("Frequency")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend()
    
    # Annotations
    sig_count = sum(1 for p in p_values if p < significance_threshold)
    ax.annotate(f'Significant: {sig_count}/{len(p_values)}',
                xy=(0.02, 0.95), xycoords='axes fraction',
                fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='#2ecc71', alpha=0.8))
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    filepath = output_path / "pvalue_distribution.png"
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"[ValidationViz] Created p-value distribution: {filepath}")
    return filepath


def create_confidence_interval_plot(
    estimates: List[Dict[str, Any]],
    title: str = "Confidence Intervals",
    output_path: Path = None
) -> Path:
    """
    Create a forest plot showing estimates with confidence intervals.
    
    Args:
        estimates: List with 'name', 'estimate', 'ci_lower', 'ci_upper' keys
        title: Plot title
        output_path: Where to save the plot
        
    Returns:
        Path to the saved plot
    """
    output_path = output_path or Path("outputs/plots")
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not estimates:
        print("[ValidationViz] No estimates to plot")
        return None
    
    fig, ax = plt.subplots(figsize=(10, max(6, len(estimates) * 0.5)))
    
    names = [e.get("name", "unknown") for e in estimates]
    values = [e.get("estimate", 0) for e in estimates]
    ci_lower = [e.get("ci_lower", e.get("estimate", 0) - 0.1) for e in estimates]
    ci_upper = [e.get("ci_upper", e.get("estimate", 0) + 0.1) for e in estimates]
    
    y_pos = range(len(names))
    
    # Error bars
    xerr = [[v - l for v, l in zip(values, ci_lower)],
            [u - v for v, u in zip(values, ci_upper)]]
    
    # Colors based on significance (CI not crossing zero)
    colors = []
    for l, u in zip(ci_lower, ci_upper):
        if l > 0 or u < 0:  # CI doesn't cross zero
            colors.append('#2ecc71')
        else:
            colors.append('#95a5a6')
    
    ax.errorbar(values, y_pos, xerr=xerr, fmt='o', markersize=8,
                color='#3498db', ecolor=colors, elinewidth=2, capsize=4)
    
    # Zero line
    ax.axvline(x=0, color='#e74c3c', linestyle='--', linewidth=1, alpha=0.7)
    
    # Labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.set_xlabel("Effect Size")
    ax.set_title(title, fontsize=14, fontweight="bold")
    
    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='#2ecc71', linewidth=2, label='Significant (CI ≠ 0)'),
        Line2D([0], [0], color='#95a5a6', linewidth=2, label='Not Significant')
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    filepath = output_path / "confidence_intervals.png"
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"[ValidationViz] Created confidence interval plot: {filepath}")
    return filepath


def create_validation_summary_plot(
    validation_results: List[Dict[str, Any]],
    title: str = "Factor Validation Summary",
    output_path: Path = None
) -> Path:
    """
    Create a summary visualization of all validation results.
    
    Args:
        validation_results: List of validation results
        title: Plot title
        output_path: Where to save the plot
        
    Returns:
        Path to the saved plot
    """
    output_path = output_path or Path("outputs/plots")
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not validation_results:
        print("[ValidationViz] No validation results to plot")
        return None
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # 1. Validation status pie chart
    validated = sum(1 for r in validation_results if r.get("significant", False))
    rejected = len(validation_results) - validated
    
    axes[0].pie([validated, rejected], 
                labels=['Validated', 'Rejected'],
                colors=['#2ecc71', '#e74c3c'],
                autopct='%1.0f%%',
                startangle=90,
                explode=(0.05, 0))
    axes[0].set_title("Validation Status")
    
    # 2. Test method distribution
    methods = {}
    for r in validation_results:
        method = r.get("test", r.get("method", "unknown"))
        methods[method] = methods.get(method, 0) + 1
    
    if methods:
        axes[1].bar(methods.keys(), methods.values(), color='#3498db', edgecolor='white')
        axes[1].set_xlabel("Test Method")
        axes[1].set_ylabel("Count")
        axes[1].set_title("Tests Used")
        axes[1].tick_params(axis='x', rotation=45)
    
    # 3. Statistic distribution
    statistics = [r.get("statistic", 0) for r in validation_results if "statistic" in r]
    if statistics:
        axes[2].hist(statistics, bins=15, color='#9b59b6', edgecolor='white', alpha=0.7)
        axes[2].axvline(x=0.3, color='#2ecc71', linestyle='--', 
                       linewidth=2, label='Moderate (0.3)')
        axes[2].set_xlabel("Test Statistic")
        axes[2].set_ylabel("Frequency")
        axes[2].set_title("Statistic Distribution")
        axes[2].legend()
    
    for ax in axes:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    
    filepath = output_path / "validation_summary.png"
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"[ValidationViz] Created validation summary: {filepath}")
    return filepath


def create_propensity_score_plot(
    propensity_data: Dict[str, Any],
    title: str = "Propensity Score Analysis",
    output_path: Path = None
) -> Path:
    """
    Create propensity score distribution and balance plots.
    
    Args:
        propensity_data: Dict with 'treated_scores', 'control_scores', 'balance'
        title: Plot title
        output_path: Where to save the plot
        
    Returns:
        Path to the saved plot
    """
    output_path = output_path or Path("outputs/plots")
    output_path.mkdir(parents=True, exist_ok=True)
    
    treated = propensity_data.get("treated_scores", [])
    control = propensity_data.get("control_scores", [])
    
    if not treated and not control:
        print("[ValidationViz] No propensity scores to plot")
        return None
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # 1. Score distributions
    if treated:
        axes[0].hist(treated, bins=20, alpha=0.6, label='Treated', color='#3498db')
    if control:
        axes[0].hist(control, bins=20, alpha=0.6, label='Control', color='#e74c3c')
    
    axes[0].set_xlabel("Propensity Score")
    axes[0].set_ylabel("Frequency")
    axes[0].set_title("Propensity Score Distribution")
    axes[0].legend()
    
    # 2. Covariate balance (if available)
    balance = propensity_data.get("balance", {})
    if balance:
        covariates = list(balance.keys())
        before = [balance[c].get("before", 0) for c in covariates]
        after = [balance[c].get("after", 0) for c in covariates]
        
        import numpy as np
        x = np.arange(len(covariates))
        width = 0.35
        
        axes[1].barh(x - width/2, before, width, label='Before Matching', color='#e74c3c', alpha=0.7)
        axes[1].barh(x + width/2, after, width, label='After Matching', color='#2ecc71', alpha=0.7)
        
        axes[1].axvline(x=0.1, color='gray', linestyle='--', linewidth=1)
        axes[1].set_yticks(x)
        axes[1].set_yticklabels(covariates)
        axes[1].set_xlabel("Standardized Mean Difference")
        axes[1].set_title("Covariate Balance")
        axes[1].legend()
    else:
        axes[1].text(0.5, 0.5, "Balance data not available",
                     ha='center', va='center', transform=axes[1].transAxes)
    
    for ax in axes:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    
    filepath = output_path / "propensity_scores.png"
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"[ValidationViz] Created propensity score plot: {filepath}")
    return filepath
