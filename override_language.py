import os
import UnityPy

def main():
    assets_path = r'from Steam\TheBardsTaleTrilogy_Data\sharedassets0.assets'
    print("Modifying langOverride.txt in sharedassets0.assets...")
    env = UnityPy.load(assets_path)
    
    found = False
    for obj in env.objects:
        if obj.type.name == 'TextAsset':
            obj_data = obj.read()
            if getattr(obj_data, 'name', '') == 'langOverride' or getattr(obj_data, 'm_Name', '') == 'langOverride':
                obj_data.m_Script = "es"
                obj_data.save()
                print("Found and replaced langOverride")
                found = True
    
    if found:
        with open(assets_path, 'wb') as f:
            f.write(env.file.save())
        print("Repacked successfully.")
    else:
        print("langOverride not found in TextAssets!")

if __name__ == '__main__':
    main()
