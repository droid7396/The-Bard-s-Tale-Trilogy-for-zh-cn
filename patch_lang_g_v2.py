import os

def patch_lang_override_g_drive():
    path = r"G:\SteamLibrary\steamapps\common\The Bard's Tale Trilogy\TheBardsTaleTrilogy_Data\sharedassets0.assets"
    
    with open(path, 'rb') as f:
        data = bytearray(f.read())
    
    target = b'es - Spanish '
    target2 = b'#es - Spanish'
    replacement = b'es\n#         '
    
    idx = data.find(target)
    if idx == -1:
        idx = data.find(target2)
        
    if idx != -1:
        data[idx:idx+len(replacement)] = replacement
        with open(path, 'wb') as f:
            f.write(data)
        print("Patched langOverride to 'es\\n#' successfully!")
    else:
        print("Target not found on G drive!")

if __name__ == '__main__':
    patch_lang_override_g_drive()
