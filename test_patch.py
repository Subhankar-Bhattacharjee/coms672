import os
import shutil
import subprocess
import re
from tqdm import tqdm

# ---- Config ----

PATCH_FOLDER = "./Dataset/QuixBugs/patches"
ORIGINAL_FOLDER = "./Dataset/QuixBugs/python_programs"
TEST_FOLDER = "./Dataset/QuixBugs/tests"
TEMP_FOLDER = "./Dataset/QuixBugs/temp_patched_files"
RESULT_FILE = "./Dataset/QuixBugs/patch_results.txt"

os.makedirs(TEMP_FOLDER, exist_ok=True)

# ---- Utility Functions ----

def load_code(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Detect trailing docstring-like block and strip it
    clean_lines = []
    for i, line in enumerate(lines):
        if re.match(r'^\s*(\"\"\"|\'\'\')', line):  # starts a docstring block
            break
        clean_lines.append(line)

    # Additional cleanup: sometimes raw lines like "Bitcount" or "Input:" appear
    for i in reversed(range(len(clean_lines))):
        if re.match(r'^\s*\w+:?\s*$', clean_lines[i]) or re.match(r'^\s*$', clean_lines[i]):
            continue
        else:
            clean_lines = clean_lines[:i+1]
            break

    return "".join(clean_lines).rstrip()


def save_code(path, code):
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

def extract_function_name(patch_code):
    match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", patch_code)
    return match.group(1) if match else None

def replace_function(original_code, patched_function, function_name):
    # Regex pattern to find function
    pattern = re.compile(rf"def\s+{function_name}\s*\(.*?:\n(?:\s+.+\n)+", re.MULTILINE)

    if re.search(pattern, original_code):
        # Replace the original function with patched function
        patched_code = re.sub(pattern, patched_function + "\n", original_code)
    else:
        # If function not found, append patched function (fail-safe)
        patched_code = original_code + "\n\n" + patched_function

    return patched_code

def fix_patch_docstring(patched_function):
    lines = patched_function.strip().splitlines()
    if not lines:
        return patched_function

    # Look for first non-indented line after the return statement or end of function
    for i, line in enumerate(lines):
        if re.match(r"^\s*return", line) or re.match(r"^\s*pass", line):
            if i + 1 < len(lines):
                trailing = lines[i + 1:]
                if trailing and not trailing[0].strip().startswith(('"""', "'''")):
                    # Indent the docstring correctly
                    indent = re.match(r"^(\s*)", lines[i]).group(1)
                    docstring = [indent + '"""'] + [indent + l for l in trailing] + [indent + '"""']
                    return "\n".join(lines[:i + 1] + docstring)
            break

    return patched_function


def run_test(test_path):
    result = subprocess.run(["python", test_path], capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

# ---- Main Agent ----

patch_files = sorted([f for f in os.listdir(PATCH_FOLDER) if f.endswith(".py")])
results = []

for patch_file in tqdm(patch_files, desc="Validating patches"):

    patch_path = os.path.join(PATCH_FOLDER, patch_file)
    original_path = os.path.join(ORIGINAL_FOLDER, patch_file)
    test_path = os.path.join(TEST_FOLDER, 'test_'+patch_file)

    if not os.path.exists(original_path):
        print(f"Original file not found for {patch_file}, skipping.")
        continue

    if not os.path.exists(test_path):
        print(f"Test file not found for {patch_file}, skipping.")
        continue

    
    patched_function = load_code(patch_path).strip()



    # Extract function name
    function_name = extract_function_name(patched_function)
    if not function_name:
        print(f"Could not find function name in patch {patch_file}, skipping.")
        results.append((patch_file, "FAIL (No function found)"))
        continue

    # Load original code
    original_code = load_code(original_path)

    # Merge patched function
    merged_code = replace_function(original_code, patched_function, function_name)

    # Save temporary merged file
    temp_file_path = os.path.join(TEMP_FOLDER, patch_file)
    save_code(temp_file_path, merged_code)

    # Backup original test file
    test_backup_path = test_path + ".bak"
    shutil.copy(test_path, test_backup_path)

    # Modify test file to import from temp patched file
    test_code = load_code(test_path)
    modified_test_code = re.sub(r"import\s+\w+", f"import sys\nsys.path.insert(0, r'{TEMP_FOLDER}')\nimport {patch_file[:-3]}", test_code, count=1)
    save_code(test_path, modified_test_code)

    # Run test
    passed, stdout, stderr = run_test(test_path)

    if passed:
        results.append((patch_file, "PASS"))
    else:
        results.append((patch_file, "FAIL"))

    # Restore original test file
    shutil.move(test_backup_path, test_path)

# ---- Save Results ----

with open(RESULT_FILE, "w", encoding="utf-8") as f:
    for patch_file, result in results:
        f.write(f"{patch_file} -> {result}\n")

print("Validation complete. Results saved to patch_results.txt")
