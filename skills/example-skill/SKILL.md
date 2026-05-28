---
name: experiment-forensics-agent
description: Diagnose machine learning experiments by reading logs, configs, metrics, and code changes.
---

# Experiment Forensics Agent

## When to use this skill

Use this skill when the user provides experiment logs, config files, metric tables, or git diffs and asks why an experiment succeeded, failed, or behaved unexpectedly.

## Inputs

The skill expects one or more of the following:

- training log
- config file
- metric CSV
- model description
- git diff
- previous experiment result

## Workflow

1. Identify the experiment objective.
2. Extract key configuration items.
3. Read metric trends.
4. Compare expected and actual behavior.
5. Locate anomalies.
6. Rank possible causes.
7. Propose the next experiment.

## Output format

Return the result in the following structure:

1. Experiment summary
2. Key observations
3. Possible causes
4. Evidence
5. Recommended next steps
6. Uncertainties

## Safety and limitations

Do not fabricate missing metrics.
Do not claim a cause unless it is supported by logs, config, or code evidence.
If information is insufficient, explicitly state what is missing.

## Example trigger

"Please analyze why this training run collapsed after epoch 8."

