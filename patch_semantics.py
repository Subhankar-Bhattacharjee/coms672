import os
import json
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# ---- Configuration ----
PATCHED_FOLDER = "./Dataset/QuixBugs/patches"
CORRECTED_FOLDER = "./Dataset/QuixBugs/correct_python_programs"
OUTPUT_JSON = "./Dataset/QuixBugs/traces/semantic_patch_eval.json"
DOCSTRING_FOLDER = "./Dataset/QuixBugs/docstrings"

MODEL_NAME = "codellama/CodeLlama-7b-Instruct-hf"
MAX_NEW_TOKENS = 200
TEMPERATURE = 0.0

# ---- Load LLM ----
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype=torch.float16
)
model.eval()

# ---- Prompt Template ----
PROMPT_TEMPLATE = """
You are a code analysis assistant.

You are given two Python functions: one is a patched version, and the other is the ground truth correct version.

Determine how different the two python codes are — i.e., do they behave the same way for all valid inputs ? Test both codes with some examples based on the docstring to see behaviour and grade the patch based on the coverage of the tests.

Input Docstring:

{docstring} 

Patched Code:

{patched}

Correct Code:

{correct}

Respond with:

- `Match`: score of behaviour match <0-3: 0 for wrong, 3 for works good, 1-3 for partial correctness, 2 for works for most test cases, 1 for works for only a few test cases>
- Short explanation

Response:
"""

# ---- Run LLM ----
def ask_llm(prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return generated.replace(prompt, "").strip()

# ---- Load Code ----
def load_code(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def load_docstring(path):
    if not os.path.exists(path):
        return "No docstring available."
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()
    
# ---- Evaluate All Patches ----
import re

def parse_response(response):
    score_match = re.search(r"Match\s*:\s*(\d+)", response, re.IGNORECASE)
    explanation_match = re.split(r"Match\s*:\s*\d+", response, maxsplit=1, flags=re.IGNORECASE)

    score = int(score_match.group(1)) if score_match else -1
    explanation = explanation_match[1].strip() if len(explanation_match) > 1 else "No explanation found."

    return score, explanation

# ---- Evaluate All Patches ----
results = []

patched_files = sorted([f for f in os.listdir(PATCHED_FOLDER) if f.endswith(".py")])

for filename in tqdm(patched_files, desc="Evaluating patches"):
    patch_path = os.path.join(PATCHED_FOLDER, filename)
    correct_path = os.path.join(CORRECTED_FOLDER, filename)

    if not os.path.exists(correct_path):
        continue

    patched_code = load_code(patch_path)
    correct_code = load_code(correct_path)
    
    basename = os.path.splitext(os.path.basename(filename))[0]
    docstring_path = os.path.join(DOCSTRING_FOLDER, basename+'.txt')
    docstring = load_docstring(docstring_path)
    
    
    prompt = PROMPT_TEMPLATE.format(docstring = docstring, patched=patched_code, correct=correct_code)
    response = ask_llm(prompt)

    score, explanation = parse_response(response)

    result = {
        "filename": filename,
        "semantic_score": score,
        "explanation": explanation
    }

    results.append(result)

# ---- Save Output ----
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print(f"Semantic patch evaluation with score saved to {OUTPUT_JSON}")

