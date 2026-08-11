import glob
import re

# The NTU backend marks a missing recording with the sentinel filename
# 沒有音檔 ("no audio file"). Older parser output wrote the AUDIO file
# attribute URL-encoded; since the 2026-07-29 parse_grammar update it is
# written decoded. Match both, or sentinel AUDIO elements leak into the
# published XML (61 leaked in the 2026-08-10 rerun audit).
SENTINEL_ENCODED = '%E6%B2%92%E6%9C%89%E9%9F%B3%E6%AA%94'
SENTINEL_DECODED = '沒有音檔'
PATTERN = re.compile(r'^\s*<AUDIO\s+file="(?:%s|%s)".*?/>\s*\n?'
                     % (re.escape(SENTINEL_ENCODED), re.escape(SENTINEL_DECODED)))

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
