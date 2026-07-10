import os

def patch_lang_override_g_drive():
    path = r"G:\SteamLibrary\steamapps\common\The Bard's Tale Trilogy\TheBardsTaleTrilogy_Data\sharedassets0.assets"
    
    with open(path, 'rb') as f:
        data = bytearray(f.read())
    
    target = b'#es - Spanish'
    replacement = b'es - Spanish '
    
    idx = data.find(target)
    if idx != -1:
        data[idx:idx+len(target)] = replacement
        with open(path, 'wb') as f:
            f.write(data)
        print("Patched langOverride successfully to 'es' on G drive!")
    else:
        # Check if already patched
        idx2 = data.find(replacement)
        if idx2 != -1:
            print("Already patched to 'es'!")
        else:
            print("Target not found on G drive!")

if __name__ == '__main__':
    patch_lang_override_g_drive()
