# from transformers import pipeline
# import os

# # ---- Config ----

# AST_FOLDER = "./Dataset/QuixBugs/ast_outputs"  # The folder containing AST txt files
# OUTPUT_FOLDER = "./Dataset/QuixBugs/buggy_detection"  # Output folder

# os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# # ---- Load model ----
# pipe = pipeline(
#     "text-generation",
#     model="bigcode/starcoder2-7b",
#     device_map="auto",
#     torch_dtype="auto"
# )

# # ---- Process AST files ----
# for ast_file in os.listdir(AST_FOLDER):
#     if not ast_file.endswith(".txt"):
#         continue

#     input_path = os.path.join(AST_FOLDER, ast_file)
#     output_path = os.path.join(OUTPUT_FOLDER, ast_file)

#     with open(input_path, "r", encoding="utf-8") as f:
#         ast_text = f.read()

#     # ---- Prepare prompt ----
#     prompt = f"""
# You are a smart assistant helping to find bugs in Python code by analyzing its AST.

# Given the AST of Python code, analyze it carefully and identify any possible bugs

# Your job is to identify the most buggy part in the code, and report:

# - The function name
# - The line number (as shown in the AST)
# - A short explanation about the bug

# Here is the AST: 
# {ast_text}

# Respond ONLY in this exact format:

# Function: <function_name>
# Buggy Line Number: <line_number>
# Explanation: <short explanation about the bug>

# If no bug is found, say:

# Function: None
# Buggy Line Number: None
# Explanation: No bug found.

# Response:
# """

#     # ---- Run the model ----
#     response = pipe(prompt, max_new_tokens=300, temperature=0.2)[0]["generated_text"]
#     response = response.strip()

#     # ---- Save result ----
#     with open(output_path, "w", encoding="utf-8") as f:
#         f.write(response + "\n")

#     print(f"Finished {ast_file} -> Saved buggy results to {output_path}")

# print("All AST files processed.")

import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# ---- Config ----
AST_FOLDER = "./Dataset/QuixBugs/ast_outputs"
OUTPUT_FOLDER = "./Dataset/QuixBugs/buggy_detection"
DOCSTRING_FOLDER = "./Dataset/QuixBugs/docstrings"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

MODEL_NAME = "codellama/CodeLlama-7b-Instruct-hf"
MAX_NEW_TOKENS = 50
TEMPERATURE = 0.0
NUM_WORKERS = 8  # You can change this based on your CPU

# ---- Load model/tokenizer ----
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype="auto",
)
model.eval()

# ---- Prompt template ----
PROMPT_TEMPLATE = """
Given the AST of Python code, analyze it carefully and identify buggy statement lines (semantical or syntax).

Below is the docstring (description of the function) and the AST of the Python function. Use this context to identify the most buggy part of the code.

Docstring:
{docstring}

AST: 
{ast_text}

Reponse format:

- The function name <function name or None>
- The line number <line number or None>
- Short explanation of bug 

If no bug is found, say:

Function: None
Buggy Line Number: None
Explanation: No bug found.

Response:
"""

# ---- Function to process single file ----
def process_ast_file(ast_file):
    input_path = os.path.join(AST_FOLDER, ast_file)
    output_path = os.path.join(OUTPUT_FOLDER, ast_file)
    docstring_path = os.path.join(DOCSTRING_FOLDER, os.path.splitext(ast_file)[0] + ".txt")
        
    with open(input_path, "r", encoding="utf-8") as f:
        ast_text = f.read()
    
    # Load docstring if exists
    if os.path.exists(docstring_path):
        with open(docstring_path, "r", encoding="utf-8") as f:
            docstring = f.read().strip()
    else:
        docstring = "No docstring available."
        
    prompt = PROMPT_TEMPLATE.format(ast_text=ast_text, docstring = docstring)

    # Tokenize input
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode response
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Remove the prompt from response if needed
    if prompt in generated_text:
        response = generated_text.replace(prompt, "").strip()
    else:
        response = generated_text.strip()

    # Save result
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response + "\n")

    return ast_file

# ---- Main parallel processing ----
def main():
    ast_files = sorted([f for f in os.listdir(AST_FOLDER) if f.endswith(".txt")])

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(process_ast_file, ast_file): ast_file for ast_file in ast_files}

        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing AST files"):
            ast_file = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error processing {ast_file}: {e}")

    print("All AST files processed.")

if __name__ == "__main__":
    main()
