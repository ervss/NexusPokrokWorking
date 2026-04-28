
import re

def check_brackets(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Very simple state machine
    i = 0
    stack = []
    
    # Regex to skip comments, strings, and regex literals
    # This is a bit rough but should be better than nothing
    patterns = [
        r'/\*.*?\*/',         # Multi-line comment
        r'//.*?\n',           # Single-line comment
        r'"(?:\\.|[^"])*"',    # Double-quoted string
        r"'(?:\\.|[^'])*'",    # Single-quoted string
        r'`(?:\\.|[^`])*`',    # Template literal
        r'/(?:\\.|[^/])+/[gimuy]*', # Regex literal (rough)
    ]
    
    # Replace all those with spaces to keep indices same
    clean_content = content
    for p in patterns:
        for match in re.finditer(p, content, re.DOTALL):
            s = match.start()
            e = match.end()
            # Check if this is really a regex or just division
            if content[s] == '/':
                # Heuristic: if previous non-space char is in [=:(,], it's a regex
                prev = content[:s].rstrip()
                if prev and prev[-1] not in '=:(,':
                    continue # Likely division
            
            clean_content = clean_content[:s] + ' ' * (e - s) + clean_content[e:]

    lines = content.splitlines(keepends=True)
    line_starts = [0]
    for line in lines:
        line_starts.append(line_starts[-1] + len(line))
    
    def get_pos(pos):
        for l, start in enumerate(line_starts):
            if start > pos:
                return l, pos - line_starts[l-1] + 1
        return len(line_starts), 0

    for i, char in enumerate(clean_content):
        if char in '([{':
            stack.append((char, i))
        elif char in ')]}':
            if not stack:
                l, c = get_pos(i)
                print(f"Unexpected {char} at line {l}, col {c}")
            else:
                opening, pos = stack.pop()
                if (opening == '(' and char != ')') or \
                   (opening == '[' and char != ']') or \
                   (opening == '{' and char != '}'):
                    l, c = get_pos(i)
                    ol, oc = get_pos(pos)
                    print(f"Mismatched {char} at line {l}, col {c} (matches {opening} from line {ol}, col {oc})")
    
    if stack:
        for opening, pos in stack:
            l, c = get_pos(pos)
            print(f"Unclosed {opening} from line {l}, col {c}")

check_brackets(r'c:\Users\Peto\Desktop\PICA\FUTURE_CLEAN_24\Nexus-Pokrok\extensions\NexusGalleryWorking\popup.js')
