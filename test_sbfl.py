import pandas as pd

# Re-load the test trace summary
file_path = "./Dataset/QuixBugs/traces/test_trace_summary.csv"
df = pd.read_csv(file_path)

# Assume last column is the outcome, rest are line traces
trace_cols = df.columns[:-1]
outcome_col = df.columns[-1]

# Count total passing and failing tests
total_pass = (df[outcome_col] == 'pass').sum()
total_fail = (df[outcome_col] == 'fail').sum()

# Initialize result list
results = []

# Compute Ochiai suspiciousness score for each line
for line in trace_cols:
    ef = ((df[line] == 1) & (df[outcome_col] == 'fail')).sum()  # executed & failed
    ep = ((df[line] == 1) & (df[outcome_col] == 'pass')).sum()  # executed & passed
    nf = ((df[line] == 0) & (df[outcome_col] == 'fail')).sum()  # not executed & failed

    if ef + ep == 0 or total_fail == 0:
        score = 0.0
    else:
        score = ef / ((ef + ep) * total_fail) ** 0.5  # Ochiai formula

    results.append({
        'line': line,
        'ef': ef,
        'ep': ep,
        'nf': nf,
        'score_ochiai': score
    })

# Convert to DataFrame and sort
results_df = pd.DataFrame(results)
results_df = results_df.sort_values(by='score_ochiai', ascending=False)

# Save to CSV
output_path = "./Dataset/QuixBugs/traces/sbfl_ochiai_results.csv"
results_df.to_csv(output_path, index=False)

