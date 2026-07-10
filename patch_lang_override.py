import os

def patch_assets():
    path = r'from Steam\TheBardsTaleTrilogy_Data\sharedassets0.assets'
    with open(path, 'rb') as f:
        data = bytearray(f.read())
    
    # We want to replace "#es - Spanish" with "es - Spanish "
    target = b'#es - Spanish'
    replacement = b'es - Spanish '
    
    idx = data.find(target)
    if idx != -1:
        data[idx:idx+len(target)] = replacement
        with open(path, 'wb') as f:
            f.write(data)
        print("Patched successfully at", idx)
    else:
        print("Target not found!")

if __name__ == '__main__':
    patch_assets()
