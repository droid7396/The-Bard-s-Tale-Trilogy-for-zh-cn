import os

def patch_level():
    path = r'from Steam\TheBardsTaleTrilogy_Data\level1'
    with open(path, 'rb') as f:
        data = bytearray(f.read())
    
    target = b'New Game'
    replacement = b'Nuevo   ' # 8 bytes exactly
    
    idx = data.find(target)
    if idx != -1:
        data[idx:idx+len(target)] = replacement
        with open(path, 'wb') as f:
            f.write(data)
        print("Patched level1 successfully at", idx)
    else:
        print("Target not found in level1!")

if __name__ == '__main__':
    patch_level()
