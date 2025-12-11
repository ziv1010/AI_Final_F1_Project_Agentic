"""
Visualization package for Universal Racing Analytics.

Provides dashboards, factor plots, and validation visualizations.
"""

from src.visualization.dashboard import (
    create_session_dashboard,
    create_comparison_dashboard
)

from src.visualization.factor_plots import (
    create_factor_importance_plot,
    create_correlation_heatmap,
    create_waterfall_plot,
    create_factor_comparison_plot
)

from src.visualization.validation_viz import (
    create_pvalue_distribution,
    create_confidence_interval_plot,
    create_validation_summary_plot,
    create_propensity_score_plot
)

__all__ = [
    # Dashboard
    "create_session_dashboard",
    "create_comparison_dashboard",
    
    # Factor plots
    "create_factor_importance_plot",
    "create_correlation_heatmap",
    "create_waterfall_plot",
    "create_factor_comparison_plot",
    
    # Validation viz
    "create_pvalue_distribution",
    "create_confidence_interval_plot",
    "create_validation_summary_plot",
    "create_propensity_score_plot"
]
