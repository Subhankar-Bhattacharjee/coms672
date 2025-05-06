# #!/usr/bin/env python3
# import ast
# import sys
# import os

# def main():
#     if len(sys.argv) < 2:
#         print("Usage: python generate_ast.py <input.py> [output.txt]")
#         sys.exit(1)

#     input_path = sys.argv[1]
#     if not input_path.endswith(".py"):
#         print("Error: input file must have a .py extension")
#         sys.exit(1)

#     # Determine output path
#     if len(sys.argv) >= 3:
#         output_path = sys.argv[2]
#     else:
#         base = os.path.splitext(os.path.basename(input_path))[0]
#         output_path = f"{base}_ast.txt"

#     # Read and parse the source file
#     with open(input_path, 'r', encoding='utf-8') as f:
#         source = f.read()
#     tree = ast.parse(source, filename=input_path)

#     # Try to pretty‐print with indentation (Python ≥3.9), else dump flat
#     try:
#         ast_dump = ast.dump(tree, indent=2)
#     except TypeError:
#         ast_dump = ast.dump(tree)

#     # Write the dump to the output file
#     with open(output_path, 'w', encoding='utf-8') as f:
#         f.write(ast_dump)

#     print(f"AST successfully written to: {output_path}")

# if __name__ == "__main__":
#     main()


# #!/usr/bin/env python3
# import ast
# import sys
# import os
# import re

# def main():
#     if len(sys.argv) < 2:
#         print("Usage: python generate_ast.py <input.py> [output.txt]")
#         sys.exit(1)

#     input_path = sys.argv[1]
#     if not input_path.endswith(".py"):
#         print("Error: input file must have a .py extension")
#         sys.exit(1)

#     # Determine output path
#     if len(sys.argv) >= 3:
#         output_path = sys.argv[2]
#     else:
#         base = os.path.splitext(os.path.basename(input_path))[0]
#         output_path = f"{base}_ast.txt"

#     # Read & parse
#     with open(input_path, 'r', encoding='utf-8') as f:
#         source = f.read()
#     tree = ast.parse(source, filename=input_path)

#     # Dump with all attributes, if possible
#     try:
#         raw = ast.dump(tree, include_attributes=True, indent=2)
#     except TypeError:
#         raw = ast.dump(tree, include_attributes=True)

#     # Strip everything except 'lineno=...' from the attribute list
#     cleaned = re.sub(
#         r",\s*(col_offset|end_lineno|end_col_offset)=[0-9]+", 
#         "", 
#         raw
#     )

#     # Write out
#     with open(output_path, 'w', encoding='utf-8') as f:
#         f.write(cleaned)

#     print(f"AST (with only line numbers) written to: {output_path}")

# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
# import os
# import ast
# import re

# # One-line bug summaries for each QuixBugs Python program
# ISSUE_DESCRIPTIONS = {
#     "bitcount.py": "Returns [list, count] instead of just the integer count.",
#     "breadth_first_search.py": "Appends neighbors to the queue before checking if they’ve been visited, causing duplicates/revisits.",
#     "bucketsort.py": "Computes bucket indices that can exceed the bucket list’s range (off-by-one).",
#     "depth_first_search.py": "Marks a node visited only on pop instead of on push, leading to potential infinite loops.",
#     "detect_cycle.py": "Calls the recursive check on the wrong node variable, so some cycles aren’t detected.",
#     "find_first_in_sorted.py": "Mis-updates the search bounds when the target is found, skipping the leftmost occurrence.",
#     "find_in_sorted.py": "Uses the wrong comparison (<= instead of <), causing off-by-one misses at the ends.",
#     "flatten.py": "Appends nested lists as whole elements rather than recursing into them.",
#     "gcd.py": "Infinite recursion when one argument is zero (base-case check is reversed).",
#     "get_factors.py": "Includes n itself in the factor list for n = 1 (should be empty/just 1).",
#     "hanoi.py": "Prints the move for the first disk twice due to a misplaced print call.",
#     "is_valid_parenthesization.py": "Fails on strings starting with a closing parenthesis because it doesn’t check stack emptiness first.",
#     "kheapsort.py": "Uses the wrong child index in heapify, so the heap property isn’t maintained.",
#     "knapsack.py": "Off-by-one in the DP table update (<= vs <), yielding incorrect max values.",
#     "kth.py": "Pivot selection returns the wrong index when all elements are equal, causing infinite recursion.",
#     "lcs_length.py": "Initializes the DP table rows/columns incorrectly, so the length count is off by one.",
#     "levenshtein.py": "Miscounts substitution cost when characters match, producing too-large distances.",
#     "lis.py": "No change — buggy and fixed are identical.",
#     "longest_common_subsequence.py": "Off-by-one error in backtracking loop, so the subsequence can be missing its first/last char.",
#     "mergesort.py": "Merge step fails when one sublist is empty, dropping remaining elements.",
#     "minimum_spanning_tree.py": "Updates the wrong key in the priority queue, causing some edges to be skipped.",
#     "next_palindrome.py": "Doesn’t propagate carry across multiple 9’s, so numbers like 1999 produce 10090 instead of 2002.",
#     "next_permutation.py": "Fails to swap the correct pair when the sequence is in descending order, so the last permutation isn’t reset.",
#     "node.py": "No change — buggy and fixed are identical.",
#     "pascal.py": "Off-by-one in row-generation loop, so each row has one too many/few entries.",
#     "possible_change.py": "Counts the same coin combination multiple times because it doesn’t advance the coin index correctly.",
#     "powerset.py": "Builds nested lists incorrectly (it appends the entire list rather than its elements).",
#     "quicksort.py": "Uses the wrong swap index in partition, so the pivot can end up in the wrong position.",
#     "rpn_eval.py": "Pops operands in the wrong order for non-commutative operators, yielding reversed results.",
#     "reverse_linked_list.py": "Fails to update the head pointer after reversal, returning None.",
#     "sieve.py": "Includes 1 in the list of primes because it starts marking at 2 only.",
#     "shortest_path_length.py": "Initializes all node distances to 0 instead of ∞, so some paths appear to have zero length.",
#     "shortest_path_lengths.py": "Same distance-initialization bug as above, affecting multi-source paths.",
#     "shortest_paths.py": "Omits the source node in the reconstructed path because it never sets a predecessor for it.",
#     "shunting_yard.py": "Doesn’t pop operators of equal precedence, so expressions like a^b^c parse wrong.",
#     "sqrt.py": "Returns a truncated float rather than an integer square root (floor) when the root is exact.",
#     "subsequences.py": "Omits the empty subsequence from the result.",
#     "to_base.py": "Off-by-one in digit conversion for bases >10, mapping 10→'A' as 9→'A' instead.",
#     "topological_ordering.py": "Reverses the final order list, producing an invalid topological sort.",
#     "wrap.py": "Breaks lines at the wrong index, splitting words incorrectly instead of at whitespace.",
# }

# # Directories (adjust paths as needed)
# INPUT_DIR = os.path.expanduser(
#     "/Users/subhankarbhattacharjee/Desktop/ISU/Spring2025/COMS672/project/test/dataset/my_dataset/python_programs"
# )
# OUTPUT_DIR = os.path.expanduser(
#     "/Users/subhankarbhattacharjee/Desktop/ISU/Spring2025/COMS672/project/test/dataset/my_dataset/ast"
# )


# def dump_clean_ast(source, filename):
#     """Parse source into AST, include lineno, strip other offsets."""
#     tree = ast.parse(source, filename=filename)
#     try:
#         raw = ast.dump(tree, include_attributes=True, indent=2)
#     except TypeError:
#         raw = ast.dump(tree, include_attributes=True)
#     cleaned = re.sub(r",\s*(col_offset|end_lineno|end_col_offset)=[0-9]+", "", raw)
#     return cleaned


# def main():
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
#     for root, dirs, files in os.walk(INPUT_DIR):
#         # Avoid recursing into OUTPUT_DIR
#         if os.path.abspath(root).startswith(os.path.abspath(OUTPUT_DIR)):
#             continue
#         for fname in files:
#             if not fname.endswith(".py"):
#                 continue
#             in_path = os.path.join(root, fname)
#             rel = os.path.relpath(in_path, INPUT_DIR)
#             base, _ = os.path.splitext(rel)
#             out_name = base + "_ast.txt"
#             out_path = os.path.join(OUTPUT_DIR, out_name)
#             os.makedirs(os.path.dirname(out_path), exist_ok=True)

#             with open(in_path, 'r', encoding='utf-8') as f:
#                 src = f.read()
#             ast_txt = dump_clean_ast(src, in_path)
#             issue = ISSUE_DESCRIPTIONS.get(fname, "No description available.")

#             with open(out_path, 'w', encoding='utf-8') as f:
#                 f.write(f"Issue Description: {issue}\n\nAST:\n{ast_txt}")

#             print(f"Wrote: {out_path}")


# if __name__ == "__main__":
#     main()


#!/usr/bin/env python3
import os
import sys
import ast
import re

ISSUE_DESCRIPTIONS = {
    "bitcount.py": "Returns [list, count] instead of just the integer count.",
    "breadth_first_search.py": "Appends neighbors to the queue before checking if they’ve been visited, causing duplicates/revisits.",
    "bucketsort.py": "Computes bucket indices that can exceed the bucket list’s range (off-by-one).",
    "depth_first_search.py": "Marks a node visited only on pop instead of on push, leading to potential infinite loops.",
    "detect_cycle.py": "Calls the recursive check on the wrong node variable, so some cycles aren’t detected.",
    "find_first_in_sorted.py": "Mis-updates the search bounds when the target is found, skipping the leftmost occurrence.",
    "find_in_sorted.py": "Uses the wrong comparison (<= instead of <), causing off-by-one misses at the ends.",
    "flatten.py": "Appends nested lists as whole elements rather than recursing into them.",
    "gcd.py": "Infinite recursion when one argument is zero (base-case check is reversed).",
    "get_factors.py": "Includes n itself in the factor list for n = 1 (should be empty/just 1).",
    "hanoi.py": "Prints the move for the first disk twice due to a misplaced print call.",
    "is_valid_parenthesization.py": "Fails on strings starting with a closing parenthesis because it doesn’t check stack emptiness first.",
    "kheapsort.py": "Uses the wrong child index in heapify, so the heap property isn’t maintained.",
    "knapsack.py": "Off-by-one in the DP table update (<= vs <), yielding incorrect max values.",
    "kth.py": "Pivot selection returns the wrong index when all elements are equal, causing infinite recursion.",
    "lcs_length.py": "Initializes the DP table rows/columns incorrectly, so the length count is off by one.",
    "levenshtein.py": "Miscounts substitution cost when characters match, producing too-large distances.",
    "lis.py": "No change — buggy and fixed are identical.",
    "longest_common_subsequence.py": "Off-by-one error in backtracking loop, so the subsequence can be missing its first/last char.",
    "mergesort.py": "Merge step fails when one sublist is empty, dropping remaining elements.",
    "minimum_spanning_tree.py": "Updates the wrong key in the priority queue, causing some edges to be skipped.",
    "next_palindrome.py": "Doesn’t propagate carry across multiple 9’s, so numbers like 1999 produce 10090 instead of 2002.",
    "next_permutation.py": "Fails to swap the correct pair when the sequence is in descending order, so the last permutation isn’t reset.",
    "node.py": "No change — buggy and fixed are identical.",
    "pascal.py": "Off-by-one in row-generation loop, so each row has one too many/few entries.",
    "possible_change.py": "Counts the same coin combination multiple times because it doesn’t advance the coin index correctly.",
    "powerset.py": "Builds nested lists incorrectly (it appends the entire list rather than its elements).",
    "quicksort.py": "Uses the wrong swap index in partition, so the pivot can end up in the wrong position.",
    "rpn_eval.py": "Pops operands in the wrong order for non-commutative operators, yielding reversed results.",
    "reverse_linked_list.py": "Fails to update the head pointer after reversal, returning None.",
    "sieve.py": "Includes 1 in the list of primes because it starts marking at 2 only.",
    "shortest_path_length.py": "Initializes all node distances to 0 instead of ∞, so some paths appear to have zero length.",
    "shortest_path_lengths.py": "Same distance-initialization bug as above, affecting multi-source paths.",
    "shortest_paths.py": "Omits the source node in the reconstructed path because it never sets a predecessor for it.",
    "shunting_yard.py": "Doesn’t pop operators of equal precedence, so expressions like a^b^c parse wrong.",
    "sqrt.py": "Returns a truncated float rather than an integer square root (floor) when the root is exact.",
    "subsequences.py": "Omits the empty subsequence from the result.",
    "to_base.py": "Off-by-one in digit conversion for bases >10, mapping 10→'A' as 9→'A' instead.",
    "topological_ordering.py": "Reverses the final order list, producing an invalid topological sort.",
    "wrap.py": "Breaks lines at the wrong index, splitting words incorrectly instead of at whitespace.",
}

# Directories
INPUT_DIR = os.path.expanduser(
    "~/Desktop/ISU/Spring2025/COMS672/project/test/dataset/my_dataset/python_programs"
)
OUTPUT_DIR = os.path.expanduser(
    "~/Desktop/ISU/Spring2025/COMS672/project/test/dataset/my_dataset/ast"
)

def node_repr(node, source_lines):
    """Return a string with node type, line number, and the full source line."""
    lineno = getattr(node, "lineno", None)
    if lineno and 1 <= lineno <= len(source_lines):
        code_line = source_lines[lineno-1].rstrip("\n")
    else:
        code_line = ""
    return f"{node.__class__.__name__} (line {lineno}): {code_line}"

def write_tree(node, source_lines, out_file, indent=""):
    """Recursively write the AST nodes with code context to the file."""
    out_file.write(indent + node_repr(node, source_lines) + "\n")
    for field, value in ast.iter_fields(node):
        if isinstance(value, ast.AST):
            write_tree(value, source_lines, out_file, indent + "    ")
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, ast.AST):
                    write_tree(item, source_lines, out_file, indent + "    ")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Walk through each Python program
    for root, dirs, files in os.walk(INPUT_DIR):
        if os.path.abspath(root).startswith(os.path.abspath(OUTPUT_DIR)):
            continue
        for fname in files:
            if not fname.endswith('.py'):
                continue
            in_path = os.path.join(root, fname)
            rel_path = os.path.relpath(in_path, INPUT_DIR)
            base, _ = os.path.splitext(rel_path)
            out_filename = base + '_ast.txt'
            out_path = os.path.join(OUTPUT_DIR, out_filename)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)

            # Read source
            with open(in_path, 'r', encoding='utf-8') as f:
                source_lines = f.readlines()
            
            # Parse and write AST with code lines
            tree = ast.parse(''.join(source_lines), filename=in_path)
            with open(out_path, 'w', encoding='utf-8') as out_file:
                # Issue description header
                issue = ISSUE_DESCRIPTIONS.get(fname, 'No description available.')
                out_file.write(f"Issue Description: {issue}\n\nAST:\n")
                write_tree(tree, source_lines, out_file)

            print(f"Wrote: {out_path}")


if __name__ == '__main__':
    main()
