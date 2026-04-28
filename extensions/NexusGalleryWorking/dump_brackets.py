
with open(r'c:\Users\Peto\Desktop\PICA\FUTURE_CLEAN_24\Nexus-Pokrok\extensions\NexusGalleryWorking\popup.js', 'rb') as f:
    lines = f.readlines()

for i, line in enumerate(lines[:200]):
    if b']' in line:
        print(f"Line {i+1}: {repr(line)}")
