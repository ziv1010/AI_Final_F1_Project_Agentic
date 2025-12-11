# Project Improvements Plan

## Professor's Feedback & Solutions

### 1. **Universal Pipeline (Not F1-Specific)**

#### Problem
- Current implementation is hardcoded for F1 data
- Driver/team names are hardcoded
- Domain-specific prompts and logic throughout

#### Solution: Domain-Agnostic Architecture

**A. Configuration-Driven Domain Specification**
```yaml
domain:
  name: "formula1"  # or "motogp", "indycar", "nascar", etc.
  entities:
    primary: "drivers"       # The main entities (drivers, riders, etc.)
    secondary: "teams"       # Secondary entities (teams, manufacturers, etc.)
  event_type: "race_weekend"  # Type of event being analyzed
  
  # Domain-specific terminology
  terminology:
    entity_primary_singular: "driver"
    entity_primary_plural: "drivers"
    entity_secondary_singular: "team"
    entity_secondary_plural: "teams"
    event: "race"
    venue: "circuit"
```

**B. Dataset Adapter Pattern**
- Each racing domain has its own adapter
- Adapters normalize data to common schema
- Pipeline works with normalized schema

**C. Dynamic Entity Recognition**
- Instead of hardcoded driver/team maps
- Use LLM to extract entities from dataset
- Cache entity mappings for performance

#### Implementation Files to Create
1. `src/adapters/base_adapter.py` - Base adapter interface
2. `src/adapters/f1_adapter.py` - F1-specific adapter
3. `src/adapters/motogp_adapter.py` - MotoGP adapter (example)
4. `src/domain_config.yaml` - Domain configuration
5. `src/nodes/universal_query_interpreter.py` - Domain-agnostic version

---

### 2. **Propensity Guardrail**

#### Problem
- No validation that factors chosen by model actually affect outcomes
- Model might hallucinate factors without statistical basis

#### Solution: Statistical Factor Validation Guardrail

**A. Hardcoded Statistical Guardrail**
- Calculate correlation between proposed factors and outcome
- Use statistical tests (correlation, ANOVA, mutual information)
- Reject factors below significance threshold

**B. Agent-Driven Guardrail (More Advanced)**
- Agent runs statistical tests autonomously
- Generates hypothesis tests
- Interprets results and filters factors

#### Guardrail Workflow
```
Factor Analyzer → Propensity Guardrail → Validated Factors → Analysis Planner
                      ↓
              Statistical Validation
              - Correlation analysis
              - Feature importance
              - Hypothesis testing
              - Causal inference checks
```

#### Implementation
1. `src/guardrails/propensity_guardrail.py` - Main guardrail
2. `src/guardrails/statistical_validator.py` - Statistical tests
3. Add guardrail node to graph between factor_analyzer and analysis_planner

#### Validation Metrics
- **Correlation Coefficient**: r > 0.3 (moderate correlation)
- **P-value**: p < 0.05 (statistical significance)
- **Mutual Information**: MI > 0.1 (information gain)
- **Feature Importance**: Top N features from trained model

---

### 3. **Additional Improvements**

#### A. Evaluation Framework
- Add metrics for agent performance
- Track accuracy of predictions
- Measure factor relevance
- Log agent decision quality

#### B. Better Error Handling
- Circuit breaker pattern for API failures
- Graceful degradation
- Better error messages with recovery suggestions

#### C. Enhanced Visualizations
- Interactive dashboards
- Factor contribution plots
- Statistical validation visualizations
- Confidence intervals on predictions

#### D. Documentation
- API documentation
- Architecture diagrams
- Usage examples for multiple domains
- Configuration guides

---

## Implementation Priority

### Phase 1: Critical (Address Professor's Feedback)
1. ✅ Domain-agnostic configuration system
2. ✅ Propensity guardrail implementation
3. ✅ Dataset adapter pattern
4. ✅ Universal entity recognition

### Phase 2: Enhanced Features
1. ✅ Evaluation framework (`src/evaluation/`)
2. ✅ Enhanced visualizations (`src/visualization/`)
3. ✅ Better error handling (`src/utils/`)
4. ✅ Performance optimizations (file-based caching)

### Phase 3: Polish
1. ✅ Documentation updated (README.md)
2. [ ] Example configurations for multiple domains
3. ✅ Testing suite (`tests/test_phase2.py`)
4. [ ] Deployment guides

---

## Key Benefits

### Universality
- Works with any racing domain (F1, MotoGP, NASCAR, IndyCar, etc.)
- Easy to extend to new domains
- No hardcoded assumptions

### Scientific Rigor
- Statistically validated factors
- Prevents hallucination
- Evidence-based analysis

### Transparency
- Shows why factors were chosen
- Provides confidence scores
- Validates assumptions

### Maintainability
- Configuration-driven
- Clean separation of concerns
- Easy to test and debug
