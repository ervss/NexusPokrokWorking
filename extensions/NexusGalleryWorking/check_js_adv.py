
import re

def check_brackets(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple state machine to skip comments, strings, and regex
    i = 0
    stack = []
    lines = content.splitlines(keepends=True)
    
    # Reconstruct line/col mapping
    line_starts = [0]
    for line in lines:
        line_starts.append(line_starts[-1] + len(line))
    
    def get_pos(pos):
        for l, start in enumerate(line_starts):
            if start > pos:
                return l, pos - line_starts[l-1] + 1
        return len(line_starts), 0

    state = 'NORMAL'
    while i < len(content):
        char = content[i]
        
        if state == 'NORMAL':
            if char == '/' and i + 1 < len(content):
                if content[i+1] == '/':
                    state = 'COMMENT_SINGLE'
                    i += 1
                elif content[i+1] == '*':
                    state = 'COMMENT_MULTI'
                    i += 1
                else:
                    # Could be regex. This is tricky in JS.
                    # A simple heuristic: if the previous non-whitespace char is 
                    # one of ( = : [ , ? or the start of the file, it's likely a regex.
                    prev_idx = i - 1
                    while prev_idx >= 0 and content[prev_idx].isspace():
                        prev_idx -= 1
                    if prev_idx < 0 or content[prev_idx] in '(=:[native,!?&|':
                         state = 'REGEX'
            elif char in '"\'`':
                state = 'STRING'
                quote_char = char
            elif char in '([{':
                stack.append((char, i))
            elif char in ')]}':
                if not stack:
                    l, c = get_pos(i)
                    print(f"Unexpected {char} at line {l}, col {c}")
                    # return # Continue to find more
                else:
                    opening, pos = stack.pop()
                    if (opening == '(' and char != ')') or \
                       (opening == '[' and char != ']') or \
                       (opening == '{' and char != '}'):
                        l, c = get_pos(i)
                        ol, oc = get_pos(pos)
                        print(f"Mismatched {char} at line {l}, col {c} (matches {opening} from line {ol}, col {oc})")
                        # return
        elif state == 'COMMENT_SINGLE':
            if char == '\n':
                state = 'NORMAL'
        elif state == 'COMMENT_MULTI':
            if char == '*' and i + 1 < len(content) and content[i+1] == '/':
                state = 'NORMAL'
                i += 1
        elif state == 'STRING':
            if char == '\\':
                i += 1
            elif char == quote_char:
                state = 'NORMAL'
        elif state == 'REGEX':
            if char == '\\':
                i += 1
            elif char == '/':
                state = 'NORMAL'
        
        i += 1
    
    if stack:
        for opening, pos in stack:
            l, c = get_pos(pos)
            print(f"Unclosed {opening} from line {l}, col {c}")

check_brackets(r'c:\Users\Peto\Desktop\PICA\FUTURE_CLEAN_24\Nexus-Pokrok\extensions\NexusGalleryWorking\popup.js')
