import csv

def extract_keys_and_en(filepath, output_csv):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    data = []
    current_key = None
    current_en_lines = []
    in_en_block = False

    # Start parsing from line 2385 (index 2384)
    start_index = 2384
    
    for i in range(start_index, len(lines)):
        line = lines[i]
        
        # Check for KEY
        if line.startswith('KEY: '):
            # Save previous block if exists
            if current_key and current_en_lines:
                en_text = ''.join(current_en_lines).strip()
                # strip leading 'EN: ' or '  EN: ' if it's there
                if en_text.startswith('EN: '):
                    en_text = en_text[4:].lstrip()
                elif en_text.startswith('EN:'):
                    en_text = en_text[3:].lstrip()
                # remove the @@ if it exists
                if en_text.startswith('@@'):
                    en_text = en_text[2:].strip()
                if en_text.endswith('@@'):
                    en_text = en_text[:-2].strip()
                    
                # Only add if there is actual English text to translate
                if en_text:
                    data.append([current_key, en_text])
            
            current_key = line[5:].strip()
            current_en_lines = []
            in_en_block = False
            continue
            
        if current_key:
            if line.startswith('  EN:'):
                in_en_block = True
                current_en_lines.append(line.strip() + '\n')
            elif in_en_block:
                # Check if it's the start of another language
                if line.startswith('  FR:') or line.startswith('  DE:') or \
                   line.startswith('  ES:') or line.startswith('  PL:') or \
                   line.startswith('  RU:') or line.startswith('KEY:'):
                    in_en_block = False
                else:
                    current_en_lines.append(line)

    # Don't forget the last one
    if current_key and current_en_lines:
        en_text = ''.join(current_en_lines).strip()
        if en_text.startswith('EN: '):
            en_text = en_text[4:].lstrip()
        elif en_text.startswith('EN:'):
            en_text = en_text[3:].lstrip()
        
        # Remove @@ blocks
        if en_text.startswith('@@'):
            en_text = en_text[2:].strip()
        if en_text.endswith('@@'):
            en_text = en_text[:-2].strip()

        if en_text:
            data.append([current_key, en_text])

    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['KEY (參考用)', 'English (遊戲原文)', 'Chinese (請填寫中文)'])
        for row in data:
            writer.writerow([row[0], row[1], ''])

    print(f"成功萃取 {len(data)} 筆需要翻譯的文本到 {output_csv}")

if __name__ == '__main__':
    extract_keys_and_en(r"extracted_text\sharedassets0.assets_btr_localization.xml.txt", "Translation_Tasks.csv")
