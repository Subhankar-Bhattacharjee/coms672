import os
import ast

def extract_trailing_docstring(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    docstrings = {}
    tree = ast.parse("".join(lines), filename=file_path)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            end_line = node.body[-1].lineno  # Last line of the function
            # Look ahead in the source file for triple-quoted string
            for i in range(end_line, min(end_line + 5, len(lines) - 1)):
                line = lines[i].strip()
                if line.startswith(('"""', "'''")):
                    doc_lines = [lines[i]]
                    quote = line[:3]
                    if line.endswith(quote) and len(line) > 6:
                        # Single line docstring
                        docstrings[node.name] = line.strip(quote).strip()
                        break
                    # Multi-line docstring
                    for j in range(i + 1, len(lines)):
                        doc_lines.append(lines[j])
                        if lines[j].strip().endswith(quote):
                            break
                    doc = "".join(doc_lines)
                    doc = doc.strip(quote).strip()
                    docstrings[node.name] = doc
                    break
    return docstrings

def extract_trailing_docstrings_from_folder(src_folder, dst_folder):
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    for filename in os.listdir(src_folder):
        if filename.endswith(".py"):
            full_path = os.path.join(src_folder, filename)
            docstrings = extract_trailing_docstring(full_path)
            if docstrings:
                doc_filename = os.path.splitext(filename)[0] + ".txt"
                output_path = os.path.join(dst_folder, doc_filename)
                with open(output_path, "w", encoding="utf-8") as out_file:
                    for func_name, doc in docstrings.items():
                        out_file.write(f"Function: {func_name}\n")
                        out_file.write(doc + "\n\n")

# Example usage
src_folder = "./Dataset/QuixBugs/python_programs"
dst_folder = "./Dataset/QuixBugs/docstrings"
extract_trailing_docstrings_from_folder(src_folder, dst_folder)

