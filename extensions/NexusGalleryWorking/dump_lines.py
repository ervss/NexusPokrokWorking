
with open(r'c:\Users\Peto\Desktop\PICA\FUTURE_CLEAN_24\Nexus-Pokrok\extensions\NexusGalleryWorking\popup.js', 'rb') as f:
    lines = f.readlines()

for i in range(110, 120):
    if i < len(lines):
        print(f"Line {i+1}: {repr(lines[i])}")
