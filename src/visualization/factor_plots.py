"""
Factor Plots for Universal Racing Analytics.

Creates visualizations for factor contributions and importance.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend


def create_factor_importance_plot(
    factors: List[Dict[str, Any]],
    title: str = "Factor Importance",
    output_path: Path = None
) -> Path:
    """
    Create a horizontal bar chart of factor importance.
    
    Args:
        factors: List of factors with 'name' and 'importance' keys
        title: Plot title
        output_path: Where to save the plot
        
    Returns:
        Path to the saved plot
    """
    output_path = output_path or Path("outputs/plots")
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not factors:
        print("[FactorPlots] No factors to plot")
        return None
    
    # Sort by importance
    sorted_factors = sorted(factors, key=lambda x: x.get("importance", 0), reverse=True)
    
    names = [f.get("name", "unknown") for f in sorted_factors]
    importances = [f.get("importance", 0) for f in sorted_factors]
    validated = [f.get("validated", False) for f in sorted_factors]
    
    # Colors based on validation
    colors = ["#3498db" if v else "#95a5a6" for v in validated]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, max(6, len(factors) * 0.4)))
    
    bars = ax.barh(names, importances, color=colors, edgecolor="white", linewidth=0.5)
    
    # Labels
    ax.set_xlabel("Importance Score")
    ax.set_title(title, fontsize=14, fontweight="bold")
    
    # Value labels on bars
    for bar, importance in zip(bars, importances):
        width = bar.get_width()
        ax.annotate(f'{importance:.2f}',
                    xy=(width, bar.get_y() + bar.get_height()/2),
                    xytext=(3, 0),
                    textcoords="offset points",
                    ha='left', va='center', fontsize=9)
    
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#3498db', label='Validated'),
        Patch(facecolor='#95a5a6', label='Not Validated')
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    # Style
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    # Save
    filepath = output_path / "factor_importance.png"
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"[FactorPlots] Created factor importance plot: {filepath}")
    return filepath


def create_correlation_heatmap(
    correlation_matrix: Dict[str, Dict[str, float]],
    title: str = "Factor Correlation Matrix",
    output_path: Path = None
) -> Path:
    """
    Create a heatmap of factor correlations.
    
    Args:
        correlation_matrix: Nested dict of correlations
        title: Plot title
        output_path: Where to save the plot
        
    Returns:
        Path to the saved plot
    """
    output_path = output_path or Path("outputs/plots")
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not correlation_matrix:
        print("[FactorPlots] No correlation data to plot")
        return None
    
    # Convert to arrays
    labels = list(correlation_matrix.keys())
    n = len(labels)
    matrix = [[correlation_matrix.get(r, {}).get(c, 0) for c in labels] for r in labels]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(max(8, n * 0.8), max(6, n * 0.6)))
    
    im = ax.imshow(matrix, cmap='RdBu_r', vmin=-1, vmax=1)
    
    # Labels
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_yticklabels(labels)
    ax.set_title(title, fontsize=14, fontweight="bold")
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Correlation')
    
    # Annotate cells
    for i in range(n):
        for j in range(n):
            val = matrix[i][j]
            color = 'white' if abs(val) > 0.5 else 'black'
            ax.annotate(f'{val:.2f}', xy=(j, i), ha='center', va='center', 
                       color=color, fontsize=8)
    
    plt.tight_layout()
    
    # Save
    filepath = output_path / "correlation_heatmap.png"
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"[FactorPlots] Created correlation heatmap: {filepath}")
    return filepath


def create_waterfall_plot(
    factors: List[Dict[str, Any]],
    baseline: float = 0,
    title: str = "Factor Contributions",
    output_path: Path = None
) -> Path:
    """
    Create a waterfall chart showing factor contributions.
    
    Args:
        factors: List of factors with 'name' and 'contribution' keys  
        baseline: Starting baseline value
        title: Plot title
        output_path: Where to save the plot
        
    Returns:
        Path to the saved plot
    """
    output_path = output_path or Path("outputs/plots")
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not factors:
        print("[FactorPlots] No factors to plot")
        return None
    
    names = ["Baseline"] + [f.get("name", "unknown") for f in factors] + ["Final"]
    contributions = [f.get("contribution", 0) for f in factors]
    
    # Calculate running totals
    values = [baseline]
    running = baseline
    for c in contributions:
        running += c
        values.append(running)
    
    # Final value (copy of last)
    values.append(values[-1])
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Colors
    colors = ['#3498db']  # Baseline
    for c in contributions:
        colors.append('#2ecc71' if c >= 0 else '#e74c3c')
    colors.append('#3498db')  # Final
    
    # Plot as step + fill
    x = range(len(names))
    bottoms = [0] + values[:-2] + [0]  # Bottom of each bar
    heights = [values[0]] + contributions + [values[-1]]  # Height of each bar
    
    # For waterfall effect, we need to track where each bar starts
    running = baseline
    bottoms = [0]
    heights = [baseline]
    
    for c in contributions:
        if c >= 0:
            bottoms.append(running)
            heights.append(c)
        else:
            bottoms.append(running + c)
            heights.append(-c)
        running += c
    
    bottoms.append(0)
    heights.append(running)
    
    bars = ax.bar(x, heights, bottom=bottoms, color=colors, edgecolor='white', linewidth=1)
    
    # Value labels
    for bar, h, b in zip(bars, heights, bottoms):
        y = b + h/2
        label = f'+{h:.1f}' if h > 0 else f'{-h:.1f}'
        ax.annotate(label, xy=(bar.get_x() + bar.get_width()/2, y),
                   ha='center', va='center', fontsize=9, fontweight='bold', color='white')
    
    # Labels
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha='right')
    ax.set_ylabel("Value")
    ax.set_title(title, fontsize=14, fontweight="bold")
    
    # Connecting lines
    for i in range(len(values) - 1):
        ax.plot([i + 0.4, i + 0.6], [values[i], values[i]], 
                color='gray', linestyle='--', linewidth=1)
    
    # Style
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    # Save
    filepath = output_path / "factor_waterfall.png"
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"[FactorPlots] Created waterfall plot: {filepath}")
    return filepath


def create_factor_comparison_plot(
    factor_sets: Dict[str, List[Dict[str, Any]]],
    title: str = "Factor Comparison",
    output_path: Path = None
) -> Path:
    """
    Create a grouped bar chart comparing factors across conditions.
    
    Args:
        factor_sets: Dict mapping condition names to factor lists
        title: Plot title  
        output_path: Where to save the plot
        
    Returns:
        Path to the saved plot
    """
    output_path = output_path or Path("outputs/plots")
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not factor_sets:
        print("[FactorPlots] No factor sets to compare")
        return None
    
    import numpy as np
    
    # Get all unique factor names
    all_factors = set()
    for factors in factor_sets.values():
        for f in factors:
            all_factors.add(f.get("name", "unknown"))
    
    factor_names = sorted(all_factors)
    conditions = list(factor_sets.keys())
    
    # Build data matrix
    data = []
    for condition in conditions:
        factors = {f.get("name"): f.get("importance", 0) for f in factor_sets[condition]}
        data.append([factors.get(name, 0) for name in factor_names])
    
    # Create plot
    fig, ax = plt.subplots(figsize=(max(10, len(factor_names) * 1.5), 6))
    
    x = np.arange(len(factor_names))
    width = 0.8 / len(conditions)
    
    colors = plt.cm.Set2(np.linspace(0, 1, len(conditions)))
    
    for i, (condition, values) in enumerate(zip(conditions, data)):
        offset = (i - len(conditions)/2 + 0.5) * width
        ax.bar(x + offset, values, width, label=condition, color=colors[i])
    
    ax.set_xlabel("Factors")
    ax.set_ylabel("Importance")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(factor_names, rotation=45, ha='right')
    ax.legend()
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    # Save
    filepath = output_path / "factor_comparison.png"
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"[FactorPlots] Created comparison plot: {filepath}")
    return filepath
