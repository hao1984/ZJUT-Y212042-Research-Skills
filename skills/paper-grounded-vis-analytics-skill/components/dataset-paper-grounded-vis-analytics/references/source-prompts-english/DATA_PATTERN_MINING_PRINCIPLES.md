# DATA PATTERN MINING PRINCIPLES

> Suitable for all pattern mining jobs of E mechanism (data-driven).
> This document is a dependency of `contracts/prompts/data_profile_v0.1.md`.
> Any mining behavior not defined in this document should be regarded as "risk behavior" and must be judged carefully.

---

## 0. Core positioning

The role of pattern mining in E-mechanisms: **Research questions in detective data worth exploring visually**.

It **is not**:
- BI analysis (not for reporting)
- Data quality check (quality is a by-product of schema profiling, not a mining goal)
- Standard statistical analysis (not intended to produce summary statistics)
- Descriptive statistical visualization (not for plotting distributions)

It **is**:
- Starting from the domain semantics of this specific data, emerge phenomena that are domain-related, non-trivial, and worthy of questioning.
- Look for "potential visualization research hooks" in the data

---

## 1. Universal Pattern vs. Data-specific Pattern

This is the **most important** concept of this document. All patterns must be classified into one of these two categories, and at least 40% of the patterns must be data-specific patterns.

### Generic Pattern (generic pattern)

Definition: **Departing from the domain semantics of this data, the pattern description itself still holds true. **

Decision question: Replace the dataset name and field name with universal placeholders (dataset X, var_1, var_2). Can the pattern description still be understood? If so, it is a universal pattern.

General patterns can emerge, but only as a starting point, not as the main body of the final output.

Common pattern example:
- "The Pearson correlation coefficient between var_1 and var_2 is 0.72"
- "The data has 3 clusters (k-means, k=3)"
- "The var_3 time series has a monthly cycle"
- "The distribution of var_4 is right-skewed (skewness=1.8)"
- "var_5 is missing 12% of the time"
- "There are 17 statistically significant outliers in var_6 (IQR method)"

### Data-specific Pattern (data-specific pattern)

Definition: ** Pattern description is meaningless without the domain semantics of this data. **

Decision question: Can the description of this pattern leave "the domain noun of this data"? If not, it is a data-specific pattern.

Data-specific pattern examples:
- "Salinity-temperature coupling reversed direction 12 hours before the storm at coastal sensing stations but not at inland stations, suggesting the existence of a regional water mass exchange boundary"
- "Hospital emergency transfer records show a one-way flow from community clinic → central hospital on Monday morning, but this direction weakens significantly at night and the reverse flow of follow-up visits strengthens"
- "The strength-conductivity trade-off of material type A is 3 times steeper than that of type B, and the steepness is strongly coupled to the temperature gradient"
- "The commit frequency of the GitHub warehouse has become more centralized among contributors 2 weeks before release, and the proportion of commits by the top 5 contributors has increased from the usual 40% to 75%."

### ⚠ WARNING: Peculiar ≠ Complex

**To determine whether a pattern is "data-specific", the criterion is whether it is inseparable from the domain semantics of this specific data, not how complex statistical methods it uses. **

- "X and Y are related" dug out by complex methods (deep learning, Bayesian networks, etc.) are still a common pattern
- "Specific subgroups deviate in specific behaviors" dug out by simple methods (group averaging) can be data-specific patterns

---

## 2. Clear definition of multi-dimensional association

"Multi-dimensional correlation" is one of the core requirements of E-mechanism mining. It has a very specific meaning:

### Definition

**Nonlinear, conditional, subset-difference coupling between ≥3 variables. **

Not an N×N correlation matrix. Not "I used multiple fields".

### Determine the problem

**"If I change the third variable, will the relationship between the first two variables change?"**

Only if the answer to this question is yes is it considered multi-dimensional correlation.

### Multi-dimensional correlation example

- "X and Y are positively related when Z=low and negatively related when Z=high" (the direction of the relationship is moderated by Z)
- "The coupling slope of X and Y is 0.3 in subgroup A and 2.1 in subgroup B" (the strength of the relationship is moderated by the subgroup)
- "X→Y in the window of time t<T, Y→X after t>T" (the causal direction of the relationship is modulated by time)

### It is not a case of multi-dimensional association

- "X, Y, Z are all related" (this is three independent bivariate correlations, not a three-dimensional coupling)
- "X affects Y, Y affects Z" (this is a chain, not a true multidimensional coupling)
- "The joint distribution of X, Y, Z is a Gaussian distribution" (this is a description, not a coupling pattern)

---

## 3. Banned Mining Outputs

The following outputs are not considered mining patterns. Even if they appear in the profile, they can only be placed in the schema profiling or data quality section. They cannot be entered into the `patterns` section, let alone support candidate RQs:

- "The distribution of field X is [uniform/normal/long-tailed/...]" → This is schema profiling
- "Data overview: N records, M fields" → This is metadata
- "Top 10 Category / High Frequency Value / Ranking" → This is ranking
- "Missing rate X%" → This is data quality
- "The mean / median / std of field X is..." → This is a descriptive statistic
- "Correlation matrix of X and Y" → This is an overview of relationships, which must be reduced to evidence of a specific pattern
- "Data can be clustered into K categories (no domain explanation)" → This is meaningless clustering

⚠ These outputs are correct in themselves, but they cannot be counted as mining results. Mining results must be able to answer "What phenomenon worthy of questioning appears in the data?"

---

## 4. Actively question user instructions

The "data description" provided by the user is important input, but is not absolutely authoritative. Agent should:

### Validate user assumptions

If the user description contains a statement such as "I think there is pattern X in the data," the agent should verify it instead of confirming it by default.

- If the data evidence supports the user hypothesis: explicitly mark "User hypothesis is supported by evidence" in the pattern
- If data evidence **refutes** user hypothesis: this is a **high value discovery**, it must be documented explicitly
- If data evidence is **insufficient**: clearly mark "User hypothesis cannot be confirmed or falsified by current data"

### Distinguish between two types of statements

In the profile output, a clear distinction must be made between:

- **User hypothesis (user_hypothesis)**: An unverified statement made by the user in the data description
- **Data evidence (data_evidence)**: The agent’s findings with statistical/numerical evidence emerged through mining

Never allow user assumptions to be used as data evidence.

### The pattern of "the user does not say it but the data itself appears" appears

The most valuable patterns are often the ones that are not mentioned in the user instructions. Agents should proactively pay attention to:
- Differences between subgroups that users do not pay attention to but are obvious in the data
- Coupling relationships that users did not expect but exist in the data
- Data quality issues that users are unaware of (not missing rates, but structural biases)

---

## 5. Mining completion standards

Agent needs to independently determine "when to stop" during the mining phase. Stop criteria:

### Necessary conditions (to be considered qualified for mining only if met)

- Emerge **≥ 5 candidate patterns**
- Among them **≥ 2 are data-specific patterns** (determined according to Section 1 of this document)
- Emerge **3-7 candidate research questions**
- Each pattern has repeatable statistical/numerical evidence (cannot only be described in natural language)

### Sufficient conditions (recommended to be met)

- There is at least 1 multi-dimensional association pattern (as defined in Section 2 of this document)
- At least 1 pattern related to the user hypothesis (verification, refutation, or extension)
- There is at least 1 pattern not mentioned in the user instructions and actively discovered by the agent.

### Stop condition

- Once the necessary conditions are met and the latest three newly mined patterns are all common patterns, you can stop
- Stage 1 mining takes more than 30 minutes, force stop and save the current results
- Computing resources (memory/CPU) hit the upper limit, stop and mark partial

---

## 6. Things not to do

### Don't make a "list of mining algorithms" and execute them one by one

If the agent understands the mining task as "complete clustering, anomaly detection, association rules, time series decomposition, PCA, t-SNE...", then it has gone down the wrong path.

Mining is detective work, not algorithm checklist execution.

This is especially true for small data sets. The computational part of small data sets should usually be short, and the real time should be spent judging which evidence can form a data-specific pattern, rather than iteratively trying alternative methods. Don’t run a bunch of generic algorithms just to “appear dark”.

Correct order:
1. Look at the data first
2. Combine with user instructions to form a conjecture about "what may be hidden in this data"
3. Verify using methods suitable for verifying conjectures
4. Emerge new conjectures and loop

Wrong order:
1. See that this is tabular data
2. Complete a set of "standard analysis methods"
3. Organize the results into pattern output

Budget discipline:

- When the necessary stopping conditions have been met, stop immediately and do not continue to dig for "there may be more" patterns.
- The middle image is not drawn by default. Save only if the graph directly helps verify or disconfirm a candidate pattern.
- Keep terminal output short; evidence is written to artifacts, not long process narratives.

### Don’t let “coverage” overwhelm “depth”

It is better to dig deep into one data-specific pattern than to superficially surface 10 common patterns.
The criterion for evaluating mining quality is how deep the deepest pattern is, not how many total patterns there are.

### Don’t make up domain knowledge outside of the data

Agents may "complement" patterns based on LLM internal domain knowledge. This is a hallucination risk.
- Allows: to surface patterns based on data and use domain knowledge to explain the possible meanings of the pattern
- Forbidden: fabricating "patterns that data should have" based on domain knowledge

Clear demarcation: interpretation is allowed, but the pattern itself must have data evidence.

### Don’t rush to give visualization direction

The output of the Mining stage is **patterns + candidate research questions**, not visual design.

Candidate research questions can include "hints in the direction of visualization", but it is not required, nor should the visual design constrain mining.

---

## 7. Anti-Dashboard in the Mining stage

Although anti-dashboard is mainly executed during the idea and demo phases, the mining phase also has responsibilities:

**Mining cannot produce the RQ of dashboard thinking**.

Candidate research question **must be rejected** of the form:
- "Data distribution overview"
- "Field dependency overview"
- "Top N rankings for each category"
- "Time series trend of X field" (only X field, no cross-cutting)
- "Statistical indicators dashboard grouped by Y"

Candidate research questions **should take the form**:
- "Under a specific subgroup/condition, some coupling or break occurs between multiple variables"
- "There is a specific boundary/phase transition/anomalous region in the data that is worth exploring its structure"
- "There is a conditional association between two seemingly unrelated dimensions"
- "A pattern assumed by the user actually exists/does not exist in an unexpected way"

---

## 8. Minimum information unit output by Pattern

Each pattern in `data_profile.yaml` must contain:

- `description`: natural language description (one sentence)
- `category`：`generic | data_specific`
- `involved_fields`: list of involved fields
- `evidence`: reproducible statistical/numerical evidence (numeric values, test statistics, subset sizes, etc.)
- `why_interesting`: Why this pattern deserves attention (one sentence)
- `relation_to_user_description`：`supports | refutes | extends | unrelated`

The last item is particularly important - it tells downstream stages how this pattern relates to user concerns.

---

## 9. Final principles for Agent

> **Mine like a detective, not like a librarian.**
>
> Your task is not to sort out what this data contains, but to discover what this data is saying.
>
> The general pattern is the starting point, not the end point.
> Data-specific patterns are targets.
>Multidimensional connections are a bonus.
>Rebutting user assumptions is a treasure trove.
> Dashboard thinking is a trap.

---

## Fixed implementation convention

-Default budget limit for mining phase: 30 minutes.
- The `evidence` field uses a free dict, but must contain verifiable values, grouping statistics, sample ids, file paths or intermediate artifact references; it cannot just write natural language judgments.
