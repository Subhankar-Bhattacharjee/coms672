import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from tqdm import tqdm

# ---- Configuration ----

BUGGY_FOLDER = "./Dataset/QuixBugs/buggy_detection"
PYTHON_FOLDER = "./Dataset/QuixBugs/python_programs"
PATCH_FOLDER = "./Dataset/QuixBugs/patches"
AST_FOLDER = "./Dataset/QuixBugs/ast_outputs"
DOCSTRING_FOLDER = "./Dataset/QuixBugs/docstrings"

os.makedirs(PATCH_FOLDER, exist_ok=True)

MODEL_NAME = "codellama/CodeLlama-7b-Instruct-hf"  # Change if needed

# ---- Load Model ----

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype=torch.float16
)
model.eval()

# ---- Utility Functions ----
import ast

def is_integer(s):
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False

def extract_code_window(code_text, buggy_line, window_size=1):
    """
    Extracts a window of code lines around the buggy line number.

    Parameters:
        code_text (str): Full code as string.
        buggy_line (int): 1-based buggy line number.
        window_size (int): Number of lines before and after buggy line to extract.

    Returns:
        str: Extracted code window as string.
    """

    lines = code_text.splitlines()
    total_lines = len(lines)

    # Calculate start and end line (clamp to valid range)
    start_line = max(buggy_line - window_size - 1, 0)
    end_line = min(buggy_line + window_size, total_lines)

    extracted_lines = lines[start_line:end_line]

    return "\n".join(extracted_lines)

def extract_function_code(code_text, function_name):
    """
    Extracts the function source code by function name from the given Python code.
    """
    try:
        tree = ast.parse(code_text)
    except SyntaxError as e:
        print("Syntax Error while parsing code:", e)
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            # Extract source lines
            lines = code_text.splitlines()
            func_lines = lines[node.lineno - 1:]  # Start from function definition

            # Stop when next function/class definition starts or end of file
            extracted_lines = []
            for line in func_lines:
                if line.startswith("def ") or line.startswith("class "):
                    if extracted_lines:
                        break
                extracted_lines.append(line)

            return "\n".join(extracted_lines)

    return None  # Function not found


def load_bug_info(path):
    info = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.lower().startswith("function:"):
                info["function"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("buggy line number:"):
                info["line"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("explanation:"):
                info["explanation"] = line.split(":", 1)[1].strip()
    return info
# def load_bug_info(path):
#     info = {}
#     entries = []
#     with open(path, "r", encoding="utf-8") as f:
#         for raw in f:
#             line = raw.strip()
#             if not line:
#                 continue
#             # remove leading dash and any surrounding whitespace
#             if line.startswith("-"):
#                 line = line[1:].lstrip()
#             entries.append(line)

#     if len(entries) >= 1:
#         info["function"] = entries[0]
#     if len(entries) >= 2:
#         info["line"] = entries[1]
#     if len(entries) >= 3:
#         # join anything from the third line onward as the explanation
#         info["explanation"] = " ".join(entries[2:])

#     return info


def load_ast(path):
    if not os.path.exists(path):
        return ""
    
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_code(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# Given following information about the bug:

# Buggy function Name: {bug_info.get('function')}
# Buggy line Number: {bug_info.get('line')}
# Bug explanation: {bug_info.get('explanation')}.  
def build_patch_prompt(bug_info, code_text, ast_text, buggy_code, code_window, docstring):
    prompt = f"""
Given the Python function docstring, the code AST, and buggy statement line in the code, write a patch to correct the bug.

Here is the code Docstring: 

{docstring} 

Here is the code AST:

{code_ast}

Here is the bug information:

Buggy function Name: {bug_info.get('function')}
Buggy line Number: {bug_info.get('line')}
Bug explanation: {bug_info.get('explanation')}

Please create patch for the bug, and return ONLY the correct code.

Response format:

<Corrected Code>

Response:
"""
    return prompt.strip()

def load_docstring(path):
    if not os.path.exists(path):
        return "No docstring available."
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def run_patch_model(prompt, max_new_tokens=256):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            # temperature=0.0,
            do_sample=False,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id
        )

    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Remove prompt part
    if prompt in generated_text:
        generated_text = generated_text.replace(prompt, "").strip()

    return generated_text

# ---- Patch Agent Main Loop ----

bug_files = sorted([f for f in os.listdir(BUGGY_FOLDER) if f.endswith(".txt")])

for bug_file in tqdm(bug_files, desc="Generating patches"):

    # Load bug info
    bug_path = os.path.join(BUGGY_FOLDER, bug_file)
    bug_info = load_bug_info(bug_path)

    # Load original python code
    code_file = bug_file.replace(".txt", ".py")
    code_path = os.path.join(PYTHON_FOLDER, code_file)
    
    ast_file = bug_file  # Same name as buggy_detection file
    ast_path = os.path.join(AST_FOLDER, ast_file)
    ast_text = load_ast(ast_path)
    
    docstring_path = os.path.join(DOCSTRING_FOLDER, bug_file)
    docstring = load_docstring(docstring_path)

    if not os.path.exists(code_path):
        print(f"Code file not found for {bug_file}, skipping.")
        continue

    code_text = load_code(code_path)
    
    
    code_ast = load_code(code_path)
    buggy_function_code = extract_function_code(code_text, bug_info.get('function'))

    buggy_line = bug_info.get('line')
    if not is_integer(buggy_line):
        patched_code = ''
    else:   
        code_window = extract_code_window(code_text, int(buggy_line))

        # Build patch prompt
        patch_prompt = build_patch_prompt(bug_info, code_text, ast_text, buggy_function_code, code_window, docstring)

        # Run patch model
        patched_code = run_patch_model(patch_prompt)

    # Save patched code
    patch_output_path = os.path.join(PATCH_FOLDER, code_file)
    with open(patch_output_path, "w", encoding="utf-8") as f:
        f.write(patched_code + "\n")

    # print(f"Saved patch for {bug_file} -> {patch_output_path}")

print("All patches generated.")
