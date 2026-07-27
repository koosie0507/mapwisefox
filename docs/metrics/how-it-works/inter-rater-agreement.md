---
title: How Inter-Rater Agreement Works
description: Learn what the Metrics agreement commands compare and how to use their results carefully.
tags:
- metrics
- inter-rater-agreement
---

# How Inter-Rater Agreement Works

Agreement measures answer different questions for discrete screening decisions and continuous quality scores. Use the measure that matches your review design, and report the files, columns, overlap, and metric variant with the result.

## Discrete screening decisions

`kappa-score` calculates Cohen's kappa for exactly two raters. It aligns the two files on their shared `id` values, removes rows with a missing decision from either rater, and compares each `-t` target column.

Cohen's kappa is a chance-corrected measure of two-rater categorical agreement. It accounts for the agreement expected from the raters' observed label frequencies. This is why it is more informative than raw percent agreement when one decision, such as `exclude`, is common. It is not a model for an arbitrary number of raters.

The command uses `include` and `exclude` as the default labels. Provide the complete label set with `--agreement-labels` when your study uses different labels. Inspect the disagreement rows, not only the summary score; label prevalence and a small common record set can make a single kappa hard to interpret.

## Continuous quality scores

`mae`, `rmse`, and `lin-ccc` treat the `-i` inputs as trusted raters. The final positional file is one rater to be evaluated against the others. For every evaluated record, the commands derive three reference values from trusted scores: their mean, minimum, and maximum. They then report one result for each reference definition and target column.

- **Mean Absolute Error (MAE)** is the average absolute distance from the reference score. Its units are the same as your scoring scale.
- **Root Mean Squared Error (RMSE)** squares differences before averaging, then takes the square root. Large score differences therefore affect it more than they affect MAE.
- **Lin's Concordance Correlation Coefficient (CCC)** evaluates both association and closeness to the equality line. Unlike ordinary correlation, it is reduced by systematic location or scale differences.

Raw correlation can be high when a rater consistently scores too high or too low. Variance alone cannot show whether raters score the same records similarly. MAE, RMSE, and CCC expose different aspects of disagreement, so no universal threshold establishes acceptable quality. Interpret their values in the context of the scale, decisions, and protocol.

## Intraclass correlation

`icc` builds a ratings matrix that includes the evaluated rater and the trusted raters. It reports the single-measure variants `ICC(1,1)`, `ICC(2,1)`, and `ICC(3,1)` for each target column. These variants use different assumptions about how raters are sampled and whether rater effects matter.

Select and report the ICC variant before analysis. Do not treat the three values as interchangeable or use a generic threshold without considering the review's rating scale and intended inference. As with other agreement measures, adequate record overlap and numeric, consistently coded scores are essential.

## References

- [McHugh, M. L. (2012). *Interrater reliability: the kappa statistic*. Biochemia Medica.](https://pmc.ncbi.nlm.nih.gov/articles/PMC3900052/)
- [Madadizadeh, F., and Bahariniya, S. (2026). *A Tutorial on Sample Size Calculation for Inter-rater and Intra-rater Agreement Studies*. Indian Journal of Psychological Medicine.](https://pmc.ncbi.nlm.nih.gov/articles/PMC12935580/)
