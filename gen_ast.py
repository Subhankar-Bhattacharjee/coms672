import ast
import os

class ASTWithTokenizedNodes(ast.NodeVisitor):
    def __init__(self, source_lines):
        self.source_lines = source_lines
        self.output = []

    def visit(self, node):
        node_type = type(node).__name__
        lineno = getattr(node, "lineno", None)

        # Get code line if possible
        if lineno is not None and 0 <= lineno - 1 < len(self.source_lines):
            code_line = self.source_lines[lineno - 1].rstrip()
        else:
            code_line = "(no code line)"

        # Add tokenized AST node format
        if lineno is not None:
            ast_line = f"<{node_type} line={lineno}> {code_line} </{node_type}>"
        else:
            ast_line = f"<{node_type} line=None> {code_line} </{node_type}>"

        self.output.append(ast_line)

        # Visit child nodes
        self.generic_visit(node)

def extract_ast_tokenized(input_file, output_file):
    # Read source file
    with open(input_file, "r", encoding="utf-8") as f:
        source = f.read()

    source_lines = source.splitlines()

    # Parse AST
    tree = ast.parse(source, filename=input_file)

    # Visit AST nodes
    visitor = ASTWithTokenizedNodes(source_lines)
    visitor.visit(tree)

    # Write tokenized AST to file
    with open(output_file, "w", encoding="utf-8") as f:
        for line in visitor.output:
            f.write(line + "\n")

    print(f"Saved AST for {input_file} -> {output_file}")

def process_directory(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".py"):
                input_path = os.path.join(root, file)

                # Use relative path to preserve subfolders
                relative_path = os.path.relpath(input_path, input_dir)
                relative_dir = os.path.dirname(relative_path)

                # Prepare output path
                output_subdir = os.path.join(output_dir, relative_dir)
                os.makedirs(output_subdir, exist_ok=True)

                filename_no_ext = os.path.splitext(os.path.basename(file))[0] + ".txt"
                output_path = os.path.join(output_subdir, filename_no_ext)

                extract_ast_tokenized(input_path, output_path)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python batch_ast_extractor.py <input_directory> <output_directory>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    process_directory(input_dir, output_dir)
