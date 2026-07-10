import os
import UnityPy

def extract_text_assets(data_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    for root, dirs, files in os.walk(data_dir):
        for file_name in files:
            if file_name.endswith('.assets') or file_name.startswith('level') or file_name == 'globalgamemanagers':
                file_path = os.path.join(root, file_name)
                try:
                    env = UnityPy.load(file_path)
                    for obj in env.objects:
                        if obj.type.name == 'TextAsset':
                            data = obj.read()
                            name = data.m_Name
                            out_name = f"{file_name}_{name}.txt"
                            out_path = os.path.join(output_dir, out_name)
                            with open(out_path, "w", encoding="utf-8", errors="ignore") as f:
                                f.write(data.m_Script)
                            # print(f"Extracted {out_name}")
                except Exception as e:
                    print(f"Failed to process {file_path}: {e}")

if __name__ == '__main__':
    data_dir = r"from Steam\TheBardsTaleTrilogy_Data"
    output_dir = r"extracted_text"
    extract_text_assets(data_dir, output_dir)
