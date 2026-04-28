
import ast

def check_syntax(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    try:
        # We use compile for JS-like syntax check if it was python, 
        # but this is JS. We can't use ast for JS.
        # But we can check for bracket balance.
        pass
    except Exception as e:
        print(e)

def check_brackets(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    stack = []
    for i, line in enumerate(lines):
        for j, char in enumerate(line):
            if char in '([{':
                stack.append((char, i + 1, j + 1))
            elif char in ')]}':
                if not stack:
                    print(f"Unexpected {char} at line {i+1}, col {j+1}")
                    return
                opening, line_no, col_no = stack.pop()
                if (opening == '(' and char != ')') or \
                   (opening == '[' and char != ']') or \
                   (opening == '{' and char != '}'):
                    print(f"Mismatched {char} at line {i+1}, col {j+1} (matches {opening} from line {line_no}, col {col_no})")
                    return
    if stack:
        opening, line_no, col_no = stack.pop()
        print(f"Unclosed {opening} from line {line_no}, col {col_no}")

check_brackets(r'c:\Users\Peto\Desktop\PICA\FUTURE_CLEAN_24\Nexus-Pokrok\extensions\NexusGalleryWorking\popup.js')
