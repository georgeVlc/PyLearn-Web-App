from bs4 import BeautifulSoup
import ast
import difflib
import textwrap


def extract_and_normalize_code(html):
    """Extracts Python code from HTML, normalizes indentation, and cleans whitespace."""
    soup = BeautifulSoup(html, 'html.parser')
    code_block = soup.find('code')
    if code_block:
        raw_code = code_block.get_text()
        return textwrap.dedent(raw_code.strip())
    return None


def get_ast_structure(code):
    """Parses Python code into an AST and simplifies the structure for get feedback."""
    try:
        tree = ast.parse(code)
        # Extract key structural elements (class/function names, args, etc.)
        return ast.dump(tree, annotate_fields=False)
    except SyntaxError as e:
        return f"Syntax Error: {e}"

def get_diff(user_code, correct_code):
    """
    Generates an HTML-formatted diff for display in a browser or web app.
    """
    user_lines = user_code.splitlines()
    correct_lines = correct_code.splitlines()
    diff = difflib.unified_diff(
        correct_lines, user_lines,
        fromfile="Correct Code", tofile="Your Code", lineterm=''
    )
    
    html_diff = []
    for line in diff:
        if line.startswith('---') or line.startswith('+++'):
            html_diff.append(f"<strong>{line}</strong>")  # Bold for file headers
        elif line.startswith('-'):
            html_diff.append(f"<span style='color: red;'>{line}</span>")  # Red
        elif line.startswith('+'):
            html_diff.append(f"<span style='color: green;'>{line}</span>")  # Green
        elif line.startswith('@@'):
            html_diff.append(f"<span style='color: cyan;'>{line}</span>")  # Cyan
        else:
            html_diff.append(f"&nbsp;&nbsp;{line}")  # Indent unchanged lines for clarity

    return "<br>".join(html_diff)


def calculate_accuracy(user_ast, correct_ast):
    """
    Calculates similarity between user and correct AST structures.
    Returns a percentage.
    """
    sm = difflib.SequenceMatcher(None, user_ast, correct_ast)
    return round(sm.ratio() * 100, 2)


def evaluate_code(user_code, correct_code_html):
    correct_code = extract_and_normalize_code(correct_code_html)
    user_ast = get_ast_structure(user_code)
    correct_ast = get_ast_structure(correct_code)
    
    # Handle syntax errors
    if "Syntax Error" in user_ast:
        return f"User code syntax error: {user_ast}"
    if "Syntax Error" in correct_ast:
        return f"Correct code syntax error: {correct_ast}"
    
    accuracy = calculate_accuracy(user_ast, correct_ast)
    return accuracy
    
def generate_feedback(user_code, correct_code_html, accuracy):
    correct_code = extract_and_normalize_code(correct_code_html)

    # Generate AST representations
    user_ast = get_ast_structure(user_code)
    correct_ast = get_ast_structure(correct_code)

    # Handle syntax errors
    if "Syntax Error" in user_ast:
        return f"User code syntax error: {user_ast}"
    if "Syntax Error" in correct_ast:
        return f"Correct code syntax error: {correct_ast}"

    diff = get_diff(user_code, correct_code)
    feedback = []
    
    if accuracy == 100:
        feedback.append("Perfect match! Your code is correct.")
    else:
        feedback.append("Your code has structural differences compared to the expected solution:")
        feedback.append(diff)

    return "\n".join(feedback)


