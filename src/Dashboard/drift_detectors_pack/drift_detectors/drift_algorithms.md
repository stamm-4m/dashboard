# Drift Detection Algorithms

| Name | Type | Class | Description | Supports Online | Parameters |
|------|------|--------|-------------|------------------|------------|
| Population Stability Index | univariate | PSI | The Population Stability Index (PSI) measures shifts in the distribution of a feature between two... | false | bins, epsilon |
| ADaptive WINdowing | univariate | Adwin | ADaptive WINdowing (ADWIN) is a drift detection method for univariate data streams. It uses a... | true | delta |
| PCA-based Change Detection | multivariate | PCA_CD | PCA-based Change Detection (PCA-CD) applies Principal Component Analysis to detect drift in... | false |  |
| KDQ-tree Drift Detection | multivariate | KDQTree | KDQ-tree is a method for detecting multivariate drift by partitioning the feature space into... | false |  |
| Kolmogorov–Smirnov Test | univariate | KSDetector | The Kolmogorov–Smirnov (KS) test is a non-parametric method for comparing two univariate... | false | alpha |
| Maximum Mean Discrepancy | multivariate | MMDDetector | Maximum Mean Discrepancy (MMD) is a nonparametric kernel-based test used to detect drift between... | false | gamma |