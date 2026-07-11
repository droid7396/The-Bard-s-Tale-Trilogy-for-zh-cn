import csv
import re
import time
from deep_translator import GoogleTranslator

input_file = 'Translation_Tasks.csv'
output_file = 'Translation_Tasks_Translated.csv'

# Regex to find placeholders like {0}, {1}
placeholder_re = re.compile(r'\{\d+\}')
# Regex to find color tags like <color=#ffff22> or </color>
tag_re = re.compile(r'<[^>]+>')

translator = GoogleTranslator(source='en', target='zh-TW')

def protect_string(s):
    placeholders = []
    def rep_ph(match):
        placeholders.append(match.group(0))
        return f" X{len(placeholders)-1}X "
        
    s = placeholder_re.sub(rep_ph, s)
    
    tags = []
    def rep_tag(match):
        tags.append(match.group(0))
        return f" Y{len(tags)-1}Y "
        
    s = tag_re.sub(rep_tag, s)
    
    # Real newlines are converted to a special string so they survive translation
    s = s.replace('\n', ' NNN ')
    
    return s, placeholders, tags

def restore_string(s, placeholders, tags):
    # Restore newlines
    s = s.replace('NNN', '\n').replace(' NNN ', '\n')
    
    # Restore tags
    for i, tag in enumerate(tags):
        s = re.sub(rf'\s*Y{i}Y\s*', tag, s)
        
    # Restore placeholders
    for i, ph in enumerate(placeholders):
        s = re.sub(rf'\s*X{i}X\s*', ph, s)
        
    return s.strip()

def process():
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        
    header = reader[0]
    rows = reader[1:]
    
    # Batch strings to translate
    batches = []
    current_batch = []
    current_length = 0
    
    # We will map each row index that needs translation to a batch item
    translation_indices = []
    
    for i, row in enumerate(rows):
        if len(row) < 3:
            row.append('')
        key, en, zh = row[0], row[1], row[2]
        
        if zh.strip() == '':
            protected_str, phs, tags = protect_string(en)
            
            # Google Translate limit is 5000 chars. We keep batch size safe around 3000
            # delimiter takes some space
            delimiter = "\n@@@\n"
            
            if current_length + len(protected_str) + len(delimiter) > 3000 and current_batch:
                batches.append(current_batch)
                current_batch = []
                current_length = 0
                
            current_batch.append((i, protected_str, phs, tags))
            current_length += len(protected_str) + len(delimiter)
            
    if current_batch:
        batches.append(current_batch)
        
    print(f"Total rows to translate: {sum(len(b) for b in batches)}")
    print(f"Total batches: {len(batches)}")
    
    for batch_idx, batch in enumerate(batches):
        print(f"Translating batch {batch_idx+1}/{len(batches)}...")
        
        texts_to_translate = [item[1] for item in batch]
        joined_text = "\n@@@\n".join(texts_to_translate)
        
        try:
            translated_joined = translator.translate(joined_text)
            translated_parts = [t.strip() for t in translated_joined.split('@@@')]
            
            if len(translated_parts) != len(batch):
                print(f"Warning: Batch {batch_idx+1} split mismatch! Expected {len(batch)} but got {len(translated_parts)}.")
                # Fallback to individual translation
                print("Falling back to individual translation for this batch...")
                for item in batch:
                    idx, p_str, phs, tags = item
                    trans = translator.translate(p_str)
                    final_zh = restore_string(trans, phs, tags)
                    rows[idx][2] = final_zh
            else:
                for item, trans in zip(batch, translated_parts):
                    idx, p_str, phs, tags = item
                    final_zh = restore_string(trans, phs, tags)
                    rows[idx][2] = final_zh
                    
        except Exception as e:
            print(f"Error in batch {batch_idx+1}: {e}")
            # Fallback
            for item in batch:
                idx, p_str, phs, tags = item
                try:
                    trans = translator.translate(p_str)
                    final_zh = restore_string(trans, phs, tags)
                    rows[idx][2] = final_zh
                except Exception as ex:
                    print(f"Failed to translate row {idx}: {ex}")
                    
        # Write to intermediate file to avoid data loss
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
            
        time.sleep(1.5) # Be polite to Google Translate
        
    print("Translation completed. Output saved to", output_file)

if __name__ == '__main__':
    process()
