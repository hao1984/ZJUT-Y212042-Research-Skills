# Skill Card: `<skill-name>`

## 1. Basic Information

| Item              | Content                                                            |
| ----------------- | ------------------------------------------------------------------ |
| Skill Name        | `<skill-name>`                                                     |
| Group             | Group `<number>`                                                   |
| Research Scenario | `<e.g., experiment diagnosis / reviewer response / dataset audit>` |
| Target Users      | `<e.g., graduate students, paper authors, project members>`        |

---

## 2. Research Pain Point

Describe the concrete research problem this skill is designed to solve.

Example:

> In machine learning research, students often generate many training logs, config files, and metric tables, but it is difficult to quickly identify why one experiment failed or why a new setting improved performance. This skill helps users diagnose experiments by analyzing logs, configurations, metrics, and code changes.

---

## 3. What This Skill Does

This skill can:

1. `<Capability 1>`
2. `<Capability 2>`
3. `<Capability 3>`
4. `<Capability 4>`

This skill does **not** aim to:

1. `<Non-goal 1>`
2. `<Non-goal 2>`

---

## 4. Required Inputs

The skill expects one or more of the following inputs:

* `<input type 1, e.g., training log>`
* `<input type 2, e.g., config file>`
* `<input type 3, e.g., metric CSV>`
* `<input type 4, e.g., manuscript section>`

Example input files:

```text
examples/input/
├── example_log.txt
├── example_config.yaml
└── example_metrics.csv
```

---

## 5. Expected Outputs

The skill produces:

* `<output 1>`
* `<output 2>`
* `<output 3>`

Example output structure:

```text
1. Task summary
2. Key findings
3. Evidence
4. Diagnosis / Analysis
5. Suggested next steps
6. Limitations
```

Example output files:

```text
examples/output/
└── example_report.md
```

---

## 6. Workflow

The skill follows this workflow:

1. Identify the user’s research task.
2. Parse the provided input materials.
3. Extract task-relevant evidence.
4. Perform structured analysis.
5. Generate a report using the required output format.
6. Check whether the conclusions are supported by evidence.
7. Clearly state uncertainties and limitations.

---

## 7. Group-Specific Feature

Describe the unique feature of this group’s skill.

Examples:

* It compares training logs with Git commit changes.
* It checks whether paper claims are supported by experimental evidence.
* It converts reviewer comments into an evidence-response matrix.
* It audits dataset leakage and train/test split problems.
* It generates ablation experiments under a limited GPU budget.

Our unique feature is:

> `<Write the group’s distinctive contribution here.>`

---

## 8. Demo Case

### Demo Input

Briefly describe the demo input.

```text
<Example: A failed training run with log file, config file, and metric table.>
```

### Demo Output

Briefly describe the demo output.

```text
<Example: The skill identified that the learning rate was too high after epoch 8 and suggested a smaller learning rate plus gradient clipping.>
```

### How to Run

```text
<Write the OpenClaw command or usage steps here.>
```

---

## 9. Evaluation

We evaluate this skill using the following criteria:

| Criterion   | Description                                              |
| ----------- | -------------------------------------------------------- |
| Usefulness  | Does it solve a real research problem?                   |
| Accuracy    | Are the conclusions supported by input evidence?         |
| Reusability | Can other students use it in similar research scenarios? |
| Clarity     | Is the output easy to read and act on?                   |
| Safety      | Does it avoid fabricating unsupported conclusions?       |

---

## 10. Limitations

This skill may fail when:

1. The input files are incomplete.
2. The user does not provide enough context.
3. The logs or results contain inconsistent information.
4. The task requires domain knowledge not included in the input.
5. The skill cannot access external tools or files required for verification.

---

## 11. Safety and Privacy

This skill should not:

1. Read private files unrelated to the research task.
2. Store or expose API keys, passwords, tokens, or personal data.
3. Automatically delete, upload, or modify important files.
4. Fabricate experimental results or paper references.
5. Claim certainty when the evidence is insufficient.

---

## 12. Future Improvements

Possible future improvements include:

1. `<Improvement 1>`
2. `<Improvement 2>`
3. `<Improvement 3>`

---

## 13. Repository Information

| Item           | Content                       |
| -------------- | ----------------------------- |
| Folder Path    | `skills/<skill-folder-name>/` |
| Main File      | `SKILL.md`                    |
| Skill Card     | `skill_card.md`               |
| Example Input  | `examples/input/`             |
| Example Output | `examples/output/`            |

