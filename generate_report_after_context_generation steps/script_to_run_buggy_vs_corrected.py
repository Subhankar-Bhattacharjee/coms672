import os
import json
import re

# the directory details
txt_folder = "/Users/subhankarbhattacharjee/Desktop/ISU/Spring2025/COMS672/project/test/dataset/my_dataset/auto/QuixBugs/buggy_detection"
buggy_folder = "/Users/subhankarbhattacharjee/Desktop/ISU/Spring2025/COMS672/project/test/dataset/my_dataset/auto/QuixBugs/python_programs"
corrected_folder = "/Users/subhankarbhattacharjee/Desktop/ISU/Spring2025/COMS672/project/test/dataset/my_dataset/auto/QuixBugs/correct_python_programs"
ast_folder = "/Users/subhankarbhattacharjee/Desktop/ISU/Spring2025/COMS672/project/test/dataset/my_dataset/auto/QuixBugs/ast"

output_jsons = []

for txt_file in os.listdir(txt_folder):
    if not txt_file.endswith(".txt"):
        continue

    base_name = os.path.splitext(txt_file)[0]
    buggy_path = os.path.join(buggy_folder, base_name + ".py")
    corrected_path = os.path.join(corrected_folder, base_name + ".py")
    txt_path = os.path.join(txt_folder, txt_file)
    ast_path = os.path.join(ast_folder, base_name + "_ast.txt")

    if not all(os.path.exists(p) for p in [buggy_path, corrected_path, txt_path, ast_path]):
        print(f"Skipping {base_name} due to missing file.")
        continue

    with open(buggy_path, 'r') as f:
        buggy_lines = f.readlines()

    with open(corrected_path, 'r') as f:
        corrected_lines = f.readlines()

    with open(txt_path, 'r') as f:
        txt_lines = [line.strip() for line in f if line.strip()]

    if len(txt_lines) < 3:
        print(f"[Warning] Not enough lines in {base_name}.txt")
        continue

    # Parse buggy line number from second line of txt
    original_buggy_line_num = -1
    match = re.search(r"\d+", txt_lines[1])
    if match:
        original_buggy_line_num = int(match.group())
        buggy_line_num = original_buggy_line_num
    else:
        print(f"[Warning] Could not parse buggy line number from '{txt_lines[1]}' in {base_name}")
        continue

    explanation = txt_lines[2]

    # If the buggy code starts with a blank line, skip it
    buggy_offset = 0
    if buggy_lines and buggy_lines[0].strip() == "":
        buggy_lines = buggy_lines[1:]
        buggy_offset = 1
        if buggy_line_num > 1:
            buggy_line_num -= 1

    # Get buggy line
    buggy_line_str = ""
    if 0 < buggy_line_num <= len(buggy_lines):
        buggy_line_str = buggy_lines[buggy_line_num - 1].strip()
    else:
        print(f"[Warning] Invalid buggy line number in {base_name}: {buggy_line_num}")

    # Extract function name
    def get_function_name(line_idx):
        for i in range(line_idx, -1, -1):
            line = buggy_lines[i].strip()
            if line.startswith("def "):
                return line.split("(")[0].replace("def", "").strip()
        return ""

    function_name = get_function_name(buggy_line_num - 1 if buggy_line_num > 0 else 0)

    # Skip leading blank lines in corrected
    corrected_leading_blanks = 0
    for line in corrected_lines:
        if line.strip() == "":
            corrected_leading_blanks += 1
        else:
            break

    # Compare aligned lines (corrected[n] vs buggy[n - corrected_leading_blanks])
    ground_truth = ""
    ground_truth_line_num = -1
    for i in range(corrected_leading_blanks, len(corrected_lines)):
        j = i - corrected_leading_blanks
        if j >= len(buggy_lines):
            break
        if buggy_lines[j] != corrected_lines[i]:
            gt_func_name = get_function_name(j)
            gt_line = corrected_lines[i].strip()  # FIXED: Use corrected line here
            ground_truth_line_num = j + 1 + buggy_offset
            if gt_line and gt_func_name:
                ground_truth = f"{ground_truth_line_num} + {gt_func_name} + {gt_line}"
            elif gt_line:
                ground_truth = f"{ground_truth_line_num} + UNKNOWN_FUNCTION + {gt_line}"
            elif gt_func_name:
                ground_truth = f"{ground_truth_line_num} + {gt_func_name} + [empty line]"
            else:
                ground_truth = f"{ground_truth_line_num} + UNKNOWN_FUNCTION + [empty line]"
            break

    # Fallback if no difference found
    if not ground_truth and buggy_lines:
        fallback_func = get_function_name(0)
        fallback_line = corrected_lines[0].strip()  # fallback to corrected
        ground_truth_line_num = 1 + buggy_offset
        ground_truth = f"{ground_truth_line_num} + {fallback_func if fallback_func else 'UNKNOWN_FUNCTION'} + {fallback_line}"

    # Determine context match
    context_match = "Yes" if ground_truth_line_num == original_buggy_line_num else "No"

    # Read AST content after "AST:"
    with open(ast_path, 'r') as f:
        lines = f.readlines()
        found_ast = False
        ast_data = ""
        for line in lines:
            if found_ast:
                ast_data += line
            if line.strip().lower() == "ast:":
                found_ast = True
        ast_data = ast_data.strip()

    json_obj = {
        "trace_id": base_name,
        "agent": "retrieval",
        "input": {
            "AST": "ast_data"
        },
        "output": {
            "buggy_line": buggy_line_str,
            "explanations": explanation,
            "function": function_name,
            "ground_truth": ground_truth,
            "context_match": context_match
        }
    }

    output_jsons.append(json_obj)

# Save consolidated JSON
output_path = os.path.join(os.path.dirname(__file__), "consolidated_op.json")
with open(output_path, "w") as f:
    json.dump(output_jsons, f, indent=2)

print(f"✅ JSON file created: {output_path}")

