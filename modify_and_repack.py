import os
import re
import UnityPy

def main():
    # 1. Modify the XML file
    xml_path = r'extracted_text\sharedassets0.assets_btr_localization.xml.txt'
    with open(xml_path, 'r', encoding='utf-8') as f:
        data = f.read()
    
    # Replace New Game, Options, Load Game, Quit Game
    data = re.sub(r'KEY: New Game\n\s+EN: New Game', r'KEY: New Game\n  EN: [NEW GAME]', data)
    data = re.sub(r'KEY: Options\n\s+EN: Options', r'KEY: Options\n  EN: [OPTIONS]', data)
    data = re.sub(r'KEY: Load Game\n\s+EN: Load Game', r'KEY: Load Game\n  EN: [LOAD GAME]', data)
    data = re.sub(r'KEY: Quit Game\n\s+EN: Quit Game', r'KEY: Quit Game\n  EN: [QUIT GAME]', data)
    
    modified_xml_path = r'extracted_text\modified_btr_localization.xml.txt'
    with open(modified_xml_path, 'w', encoding='utf-8') as f:
        f.write(data)
    
    # 2. Backup sharedassets0.assets
    assets_path = r'from Steam\TheBardsTaleTrilogy_Data\sharedassets0.assets'
    backup_path = assets_path + '.bak'
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy2(assets_path, backup_path)
    
    # 3. Repack
    print("Repacking...")
    env = UnityPy.load(assets_path)
    for obj in env.objects:
        if obj.type.name == 'TextAsset':
            obj_data = obj.read()
            if getattr(obj_data, 'name', '') == 'btr_localization.xml' or getattr(obj_data, 'm_Name', '') == 'btr_localization.xml':
                obj_data.m_Script = data
                obj_data.save()
                print("Found and replaced btr_localization.xml")
    
    # Save the file
    with open(assets_path, 'wb') as f:
        f.write(env.file.save())
    print("Repacked successfully.")

if __name__ == '__main__':
    main()
