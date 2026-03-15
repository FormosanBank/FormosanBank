import os
import xml.etree.ElementTree as ET
import regex as re

xml_dir = "Final_XML"

for filename in os.listdir(xml_dir):
    if filename.endswith(".xml"):
        path = os.path.join(xml_dir, filename)
        tree = ET.parse(path)
        root = tree.getroot()
        changed = False

        for form in root.iter("FORM"):
            if form.text:
                # First: Replace any letter followed by final ' with letter + ?
                new_text = re.sub(r"(\p{L})'$", r"\1?", form.text)

                # Second: Replace a ' before a final " with ?
                new_text = re.sub(r"'(\")$", r"?\1", new_text)

                # Third: Replace any letter followed by a ' followed by a " with a ?
                new_text = re.sub(r"(\p{L})'(\")", r"\1?\2", new_text)
                if new_text != form.text:
                    form.text = new_text
                    changed = True

        for phon in root.iter("PHON"):
            if phon.text:
                # First: Replace any letter followed by final ' with letter + ?
                new_text = re.sub(r"(\p{L})ʔ$", r"\1", phon.text)

                # Second: Replace a ' before a final " with ?
                new_text = re.sub(r"ʔ(\")$", r"\1", new_text)

                # Third: Replace any letter followed by a ' followed by a " with a ?
                new_text = re.sub(r"(\p{L})ʔ(\")", r"\1\2", new_text)
                if new_text != phon.text:
                    phon.text = new_text
                    changed = True

        if changed:
            tree.write(path, encoding="utf-8", xml_declaration=True)