import glob
import re

SENTINEL = '%E6%B2%92%E6%9C%89%E9%9F%B3%E6%AA%94'
# Matches the entire AUDIO element line with the "no audio" sentinel
PATTERN = re.compile(r'^\s*<AUDIO\s+file="%s".*?/>\s*\n?' % re.escape(SENTINEL))

xml_files = glob.glob('Final_XML/**/*.xml', recursive=True)

total_removed = 0

for xml_file in sorted(xml_files):
    with open(xml_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    removed = 0
    for line in lines:
        if PATTERN.match(line):
            removed += 1
        else:
            new_lines.append(line)

    if removed:
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"  {xml_file}: removed {removed} element(s)")
        total_removed += removed

print(f"\nDone. Total removed: {total_removed}")
