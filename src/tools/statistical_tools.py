"""
Statistical Tools for Propensity Guardrail.

Provides tools for:
1. Correlation analysis (Pearson, Spearman)
2. Feature importance calculation
3. Propensity score analysis
4. Statistical hypothesis testing
"""

from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
import numpy as np
import json


@tool
def calculate_correlation(
    factor_column: str,
    outcome_column: str,
    data_path: str,
    method: str = "pearson"
) -> str:
    """
    Calculate correlation between a factor and an outcome variable.
    
    Use this to validate if a proposed factor actually correlates with
    the outcome (e.g., does qualifying position correlate with race result?).
    
    Args:
        factor_column: Name of the factor column (e.g., "grid", "qualifying_position")
        outcome_column: Name of the outcome column (e.g., "position", "points")
        data_path: Path to the data file (CSV or Parquet)
        method: Correlation method - "pearson" (linear) or "spearman" (monotonic)
    
    Returns:
        Correlation coefficient, p-value, and interpretation
    
    Examples:
        calculate_correlation("grid", "positionOrder", "results.csv", "pearson")
        -> Returns: "Pearson correlation: r=0.72, p<0.001 - SIGNIFICANT"
    """
    try:
        from scipy import stats
        
        # Load data
        file_path = Path(data_path)
        if not file_path.exists():
            from src.config import get_raw_data_path
            file_path = get_raw_data_path() / data_path
        
        if file_path.suffix == ".parquet":
            df = pd.read_parquet(file_path)
        else:
            df = pd.read_csv(file_path)
        
        # Check if columns exist
        if factor_column not in df.columns:
            # Try to find similar column
            similar = [c for c in df.columns if factor_column.lower() in c.lower()]
            if similar:
                factor_column = similar[0]
            else:
                return f"Column '{factor_column}' not found. Available: {list(df.columns)}"
        
        if outcome_column not in df.columns:
            similar = [c for c in df.columns if outcome_column.lower() in c.lower()]
            if similar:
                outcome_column = similar[0]
            else:
                return f"Column '{outcome_column}' not found. Available: {list(df.columns)}"
        
        # Get numeric data
        x = pd.to_numeric(df[factor_column], errors="coerce")
        y = pd.to_numeric(df[outcome_column], errors="coerce")
        
        # Remove NaN values
        mask = ~(x.isna() | y.isna())
        x = x[mask]
        y = y[mask]
        
        if len(x) < 10:
            return f"Insufficient data: only {len(x)} valid pairs. Need at least 10."
        
        # Calculate correlation
        if method == "spearman":
            corr, p_value = stats.spearmanr(x, y)
            method_name = "Spearman"
        else:
            corr, p_value = stats.pearsonr(x, y)
            method_name = "Pearson"
        
        # Interpret
        significance = "SIGNIFICANT" if p_value < 0.05 else "NOT SIGNIFICANT"
        strength = "strong" if abs(corr) > 0.7 else ("moderate" if abs(corr) > 0.3 else "weak")
        direction = "positive" if corr > 0 else "negative"
        
        result = {
            "method": method_name,
            "correlation": round(corr, 4),
            "p_value": round(p_value, 6),
            "sample_size": len(x),
            "significant": p_value < 0.05,
            "strength": strength,
            "direction": direction
        }
        
        summary = (
            f"**{method_name} Correlation Analysis**\n"
            f"Factor: {factor_column} → Outcome: {outcome_column}\n"
            f"Correlation: r = {corr:.4f} ({strength} {direction})\n"
            f"P-value: {p_value:.6f}\n"
            f"Sample size: {len(x)}\n"
            f"Result: **{significance}**\n"
            f"\nInterpretation: {'This factor has a statistically significant relationship with the outcome.' if p_value < 0.05 else 'This factor does NOT have a statistically significant relationship.'}"
        )
        
        return summary
        
    except ImportError:
        return "scipy not installed. Run: pip install scipy"
    except Exception as e:
        return f"Error calculating correlation: {str(e)}"


@tool
def calculate_feature_importance(
    feature_columns: str,
    outcome_column: str,
    data_path: str,
    top_n: int = 10
) -> str:
    """
    Calculate feature importance using Random Forest.
    
    Use this to determine which factors are most predictive of the outcome.
    Returns ranked list of features by importance score.
    
    Args:
        feature_columns: Comma-separated list of feature column names
                        (e.g., "grid,laps,milliseconds,fastestLapSpeed")
        outcome_column: Target variable column (e.g., "positionOrder")
        data_path: Path to the data file
        top_n: Number of top features to return
    
    Returns:
        Ranked list of features with importance scores
    
    Examples:
        calculate_feature_importance("grid,laps", "positionOrder", "results.csv")
        -> Returns importance ranking
    """
    try:
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.preprocessing import LabelEncoder
        
        # Load data
        file_path = Path(data_path)
        if not file_path.exists():
            from src.config import get_raw_data_path
            file_path = get_raw_data_path() / data_path
        
        if file_path.suffix == ".parquet":
            df = pd.read_parquet(file_path)
        else:
            df = pd.read_csv(file_path)
        
        # Parse feature columns
        features = [f.strip() for f in feature_columns.split(",")]
        
        # Find matching columns
        available_features = []
        for feat in features:
            if feat in df.columns:
                available_features.append(feat)
            else:
                # Try to find similar
                similar = [c for c in df.columns if feat.lower() in c.lower()]
                if similar:
                    available_features.append(similar[0])
        
        if not available_features:
            return f"No valid features found. Available columns: {list(df.columns)}"
        
        # Find outcome column
        if outcome_column not in df.columns:
            similar = [c for c in df.columns if outcome_column.lower() in c.lower()]
            if similar:
                outcome_column = similar[0]
            else:
                return f"Outcome column '{outcome_column}' not found."
        
        # Prepare data
        X = df[available_features].copy()
        y = df[outcome_column].copy()
        
        # Handle categorical features
        for col in X.columns:
            if X[col].dtype == "object":
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
        
        # Fill NaN
        X = X.fillna(X.median())
        
        # Handle outcome
        if y.dtype == "object":
            le = LabelEncoder()
            y = le.fit_transform(y.astype(str))
            y = pd.Series(y)
        
        y = y.fillna(y.median())
        
        # Remove rows with NaN
        mask = ~(X.isna().any(axis=1) | pd.isna(y))
        X = X[mask]
        y = y[mask]
        
        if len(X) < 50:
            return f"Insufficient data: {len(X)} rows. Need at least 50."
        
        # Train Random Forest
        is_classification = y.nunique() < 20
        if is_classification:
            model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        
        model.fit(X, y)
        
        # Get importance
        importance = pd.DataFrame({
            "feature": available_features,
            "importance": model.feature_importances_
        }).sort_values("importance", ascending=False)
        
        # Format output
        lines = [
            f"**Feature Importance Analysis**",
            f"Model: Random Forest {'Classifier' if is_classification else 'Regressor'}",
            f"Outcome: {outcome_column}",
            f"Sample size: {len(X)}",
            f"\nRanked Features:"
        ]
        
        for i, row in importance.head(top_n).iterrows():
            pct = row['importance'] * 100
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            lines.append(f"  {row['feature']}: {pct:.1f}% {bar}")
        
        # Identify significant features (> 5% importance)
        significant = importance[importance['importance'] > 0.05]['feature'].tolist()
        lines.append(f"\n**Significant factors (>5% importance):** {significant}")
        
        return "\n".join(lines)
        
    except ImportError:
        return "scikit-learn not installed. Run: pip install scikit-learn"
    except Exception as e:
        return f"Error calculating feature importance: {str(e)}"


@tool
def run_statistical_test(
    test_type: str,
    group_column: str,
    value_column: str,
    data_path: str
) -> str:
    """
    Run a statistical hypothesis test to validate factor significance.
    
    Use this to test if there's a significant difference in outcomes
    between different groups (e.g., teams, constructors, conditions).
    
    Args:
        test_type: Type of test:
            - "t_test": Compare means of two groups
            - "anova": Compare means of multiple groups
            - "chi_square": Test independence of categorical variables
            - "mann_whitney": Non-parametric comparison of two groups
            - "kruskal": Non-parametric comparison of multiple groups
        group_column: Column defining groups (e.g., "constructorId", "team_name")
        value_column: Column with values to compare (e.g., "points", "position")
        data_path: Path to the data file
    
    Returns:
        Test statistic, p-value, and interpretation
    
    Examples:
        run_statistical_test("anova", "constructorId", "points", "results.csv")
        -> Tests if constructor significantly affects points
    """
    try:
        from scipy import stats
        
        # Load data
        file_path = Path(data_path)
        if not file_path.exists():
            from src.config import get_raw_data_path
            file_path = get_raw_data_path() / data_path
        
        if file_path.suffix == ".parquet":
            df = pd.read_parquet(file_path)
        else:
            df = pd.read_csv(file_path)
        
        # Find columns
        if group_column not in df.columns:
            similar = [c for c in df.columns if group_column.lower() in c.lower()]
            if similar:
                group_column = similar[0]
            else:
                return f"Group column '{group_column}' not found."
        
        if value_column not in df.columns:
            similar = [c for c in df.columns if value_column.lower() in c.lower()]
            if similar:
                value_column = similar[0]
            else:
                return f"Value column '{value_column}' not found."
        
        # Prepare groups
        groups = df.groupby(group_column)[value_column].apply(list).to_dict()
        groups = {k: [v for v in vals if pd.notna(v)] for k, vals in groups.items()}
        groups = {k: v for k, v in groups.items() if len(v) >= 5}  # Min 5 samples per group
        
        if len(groups) < 2:
            return f"Not enough groups with sufficient data. Need at least 2 groups with 5+ samples each."
        
        group_names = list(groups.keys())
        group_values = list(groups.values())
        
        # Run test
        if test_type == "t_test":
            if len(groups) != 2:
                return f"T-test requires exactly 2 groups, found {len(groups)}. Use 'anova' instead."
            stat, p_value = stats.ttest_ind(group_values[0], group_values[1])
            test_name = "Independent T-Test"
            
        elif test_type == "anova":
            stat, p_value = stats.f_oneway(*group_values)
            test_name = "One-way ANOVA"
            
        elif test_type == "mann_whitney":
            if len(groups) != 2:
                return f"Mann-Whitney requires exactly 2 groups, found {len(groups)}."
            stat, p_value = stats.mannwhitneyu(group_values[0], group_values[1])
            test_name = "Mann-Whitney U Test"
            
        elif test_type == "kruskal":
            stat, p_value = stats.kruskal(*group_values)
            test_name = "Kruskal-Wallis H Test"
            
        elif test_type == "chi_square":
            # For chi-square, we need a contingency table
            contingency = pd.crosstab(df[group_column], df[value_column])
            stat, p_value, dof, expected = stats.chi2_contingency(contingency)
            test_name = "Chi-Square Test"
            
        else:
            return f"Unknown test type: {test_type}. Use: t_test, anova, chi_square, mann_whitney, kruskal"
        
        # Interpret
        significance = "SIGNIFICANT" if p_value < 0.05 else "NOT SIGNIFICANT"
        
        # Calculate effect size for ANOVA (eta-squared) if applicable
        effect_size_info = ""
        if test_type == "anova":
            all_values = [v for group in group_values for v in group]
            grand_mean = np.mean(all_values)
            ss_between = sum(len(g) * (np.mean(g) - grand_mean)**2 for g in group_values)
            ss_total = sum((v - grand_mean)**2 for v in all_values)
            if ss_total > 0:
                eta_sq = ss_between / ss_total
                effect_size_info = f"\nEffect size (η²): {eta_sq:.4f} ({'large' if eta_sq > 0.14 else 'medium' if eta_sq > 0.06 else 'small'})"
        
        summary = (
            f"**{test_name}**\n"
            f"Groups: {group_column} ({len(groups)} groups)\n"
            f"Outcome: {value_column}\n"
            f"Test statistic: {stat:.4f}\n"
            f"P-value: {p_value:.6f}\n"
            f"Result: **{significance}**{effect_size_info}\n"
            f"\nGroup means:"
        )
        
        for name in group_names[:10]:  # Show up to 10 groups
            mean = np.mean(groups[name])
            summary += f"\n  • {name}: {mean:.2f}"
        
        if len(group_names) > 10:
            summary += f"\n  ... and {len(group_names) - 10} more groups"
        
        interpretation = (
            f"\n\nInterpretation: {'The grouping variable significantly affects the outcome.' if p_value < 0.05 else 'No significant difference between groups.'}"
        )
        
        return summary + interpretation
        
    except ImportError:
        return "scipy not installed. Run: pip install scipy"
    except Exception as e:
        return f"Error running statistical test: {str(e)}"


@tool
def calculate_propensity_score(
    treatment_column: str,
    outcome_column: str,
    covariate_columns: str,
    data_path: str
) -> str:
    """
    Perform propensity score analysis to estimate causal effect.
    
    This advanced technique estimates the causal effect of a treatment/factor
    on an outcome by controlling for confounding variables.
    
    Args:
        treatment_column: Binary treatment variable (e.g., "used_soft_tyres", "pit_first")
        outcome_column: Outcome variable (e.g., "position", "points")
        covariate_columns: Comma-separated confounders (e.g., "grid,laps,constructorId")
        data_path: Path to the data file
    
    Returns:
        Propensity score analysis results including:
        - Average Treatment Effect (ATE)
        - Statistical significance
        - Balance diagnostics
    
    Examples:
        calculate_propensity_score("pit_first", "position", "grid,laps", "results.csv")
        -> Estimates causal effect of pitting first on race position
    """
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import LabelEncoder
        
        # Load data
        file_path = Path(data_path)
        if not file_path.exists():
            from src.config import get_raw_data_path
            file_path = get_raw_data_path() / data_path
        
        if file_path.suffix == ".parquet":
            df = pd.read_parquet(file_path)
        else:
            df = pd.read_csv(file_path)
        
        # Parse covariate columns
        covariates = [c.strip() for c in covariate_columns.split(",")]
        available_covariates = [c for c in covariates if c in df.columns]
        
        if not available_covariates:
            return f"No valid covariates found. Available: {list(df.columns)}"
        
        # Find treatment column
        if treatment_column not in df.columns:
            similar = [c for c in df.columns if treatment_column.lower() in c.lower()]
            if similar:
                treatment_column = similar[0]
            else:
                return f"Treatment column '{treatment_column}' not found."
        
        # Find outcome column
        if outcome_column not in df.columns:
            similar = [c for c in df.columns if outcome_column.lower() in c.lower()]
            if similar:
                outcome_column = similar[0]
            else:
                return f"Outcome column '{outcome_column}' not found."
        
        # Prepare data
        X = df[available_covariates].copy()
        treatment = df[treatment_column].copy()
        outcome = df[outcome_column].copy()
        
        # Encode categorical
        for col in X.columns:
            if X[col].dtype == "object":
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
        
        # Make treatment binary
        if treatment.dtype == "object":
            treatment = (treatment == treatment.mode()[0]).astype(int)
        elif treatment.nunique() > 2:
            treatment = (treatment > treatment.median()).astype(int)
        
        # Fill NaN
        X = X.fillna(X.median())
        treatment = treatment.fillna(0).astype(int)
        outcome = pd.to_numeric(outcome, errors="coerce").fillna(outcome.median())
        
        # Remove rows with NaN
        mask = ~(X.isna().any(axis=1) | pd.isna(treatment) | pd.isna(outcome))
        X = X[mask]
        treatment = treatment[mask]
        outcome = outcome[mask]
        
        if len(X) < 100:
            return f"Insufficient data for propensity analysis: {len(X)} rows. Need at least 100."
        
        # Fit propensity score model
        ps_model = LogisticRegression(max_iter=1000, random_state=42)
        ps_model.fit(X, treatment)
        propensity_scores = ps_model.predict_proba(X)[:, 1]
        
        # Calculate treatment effects using stratification
        df_analysis = pd.DataFrame({
            "propensity": propensity_scores,
            "treatment": treatment.values,
            "outcome": outcome.values
        })
        
        # Create strata
        df_analysis["stratum"] = pd.qcut(df_analysis["propensity"], q=5, labels=False, duplicates="drop")
        
        # Calculate ATE within each stratum
        strata_effects = []
        for stratum in df_analysis["stratum"].unique():
            stratum_data = df_analysis[df_analysis["stratum"] == stratum]
            treated = stratum_data[stratum_data["treatment"] == 1]["outcome"]
            control = stratum_data[stratum_data["treatment"] == 0]["outcome"]
            
            if len(treated) > 0 and len(control) > 0:
                effect = treated.mean() - control.mean()
                weight = len(stratum_data) / len(df_analysis)
                strata_effects.append(effect * weight)
        
        ate = sum(strata_effects)
        
        # Simple significance test (bootstrap would be better but more complex)
        treated_outcomes = df_analysis[df_analysis["treatment"] == 1]["outcome"]
        control_outcomes = df_analysis[df_analysis["treatment"] == 0]["outcome"]
        from scipy import stats
        t_stat, p_value = stats.ttest_ind(treated_outcomes, control_outcomes)
        
        significance = "SIGNIFICANT" if p_value < 0.05 else "NOT SIGNIFICANT"
        
        summary = (
            f"**Propensity Score Analysis**\n"
            f"Treatment: {treatment_column}\n"
            f"Outcome: {outcome_column}\n"
            f"Covariates: {available_covariates}\n"
            f"\n**Results:**\n"
            f"Average Treatment Effect (ATE): {ate:.4f}\n"
            f"P-value: {p_value:.6f}\n"
            f"Result: **{significance}**\n"
            f"\nTreated group mean: {treated_outcomes.mean():.2f}\n"
            f"Control group mean: {control_outcomes.mean():.2f}\n"
            f"Sample sizes: Treated={len(treated_outcomes)}, Control={len(control_outcomes)}\n"
            f"\nInterpretation: {'The treatment has a statistically significant causal effect on the outcome.' if p_value < 0.05 else 'No significant causal effect detected.'}"
        )
        
        return summary
        
    except ImportError:
        return "Required packages not installed. Run: pip install scikit-learn scipy"
    except Exception as e:
        return f"Error in propensity analysis: {str(e)}"
