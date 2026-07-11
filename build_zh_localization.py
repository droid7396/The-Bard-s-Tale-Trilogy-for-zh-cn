import csv
import sys
import os

def build_localization(csv_path, original_xml_path, output_xml_path):
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        return
    if not os.path.exists(original_xml_path):
        print(f"Error: Original XML file not found: {original_xml_path}")
        return

    # 1. Load CSV
    translations = {}
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) >= 3:
                key = row[0].strip()
                en_text = row[1].strip()
                zh_text = row[2].strip()
                if key and zh_text:
                    translations[key] = (en_text, zh_text)

    print(f"Loaded {len(translations)} translations from {csv_path}")

    # 2. Process XML
    with open(original_xml_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    output_lines = []
    current_key = None
    skip_en_block = False
    skip_fr_block = False

    i = 0
    replaced_count = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith('KEY: '):
            current_key = line[5:].strip()
            output_lines.append(line)
            i += 1
            continue

        if current_key and line.startswith('  EN:'):
            if current_key in translations:
                en_text, zh_text = translations[current_key]
                if '\n' in zh_text:
                    output_lines.append(f"  EN:@@\n{zh_text}\n@@\n")
                else:
                    if line.startswith('  EN:@@') and not line.strip().endswith('@@'):
                        output_lines.append(f"  EN:@@\n{zh_text}\n@@\n")
                    elif line.startswith('  EN:@@') and line.strip().endswith('@@'):
                        output_lines.append(f"  EN:@@{zh_text}@@\n")
                    else:
                        output_lines.append(f"  EN: {zh_text}\n")
                skip_en_block = True
                replaced_count += 1
            else:
                output_lines.append(line)
                skip_en_block = False
            i += 1
            continue

        if skip_en_block:
            if line.startswith('  FR:') or line.startswith('  DE:') or \
               line.startswith('  ES:') or line.startswith('  PL:') or \
               line.startswith('  RU:') or line.startswith('KEY: ') or \
               line.startswith('===================='):
                skip_en_block = False
            else:
                i += 1
                continue

        if current_key and line.startswith('  FR:'):
            if current_key in translations:
                en_text, zh_text = translations[current_key]
                if '\n' in en_text:
                    output_lines.append(f"  FR:@@\n{en_text}\n@@\n")
                else:
                    if line.startswith('  FR:@@') and not line.strip().endswith('@@'):
                        output_lines.append(f"  FR:@@\n{en_text}\n@@\n")
                    elif line.startswith('  FR:@@') and line.strip().endswith('@@'):
                        output_lines.append(f"  FR:@@{en_text}@@\n")
                    else:
                        output_lines.append(f"  FR: {en_text}\n")
                skip_fr_block = True
            else:
                output_lines.append(line)
                skip_fr_block = False
            i += 1
            continue

        if skip_fr_block:
            if line.startswith('  DE:') or \
               line.startswith('  ES:') or line.startswith('  PL:') or \
               line.startswith('  RU:') or line.startswith('KEY: ') or \
               line.startswith('===================='):
                skip_fr_block = False
            else:
                i += 1
                continue

        output_lines.append(line)
        i += 1

    with open(output_xml_path, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    print(f"Generated {output_xml_path} with {replaced_count} replaced translations.")

if __name__ == '__main__':
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "Translation_Tasks_LLM.csv"
    orig_path = sys.argv[2] if len(sys.argv) > 2 else "extracted_text/sharedassets0.assets_btr_localization.xml.txt"
    out_path = sys.argv[3] if len(sys.argv) > 3 else "ZHLocalizer/btr_localization_zh.txt"
    build_localization(csv_path, orig_path, out_path)
