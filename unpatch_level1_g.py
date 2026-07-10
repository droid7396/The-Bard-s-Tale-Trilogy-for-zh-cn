import os

def unpatch_level_g():
    path = r"G:\SteamLibrary\steamapps\common\The Bard's Tale Trilogy\TheBardsTaleTrilogy_Data\level1"
    with open(path, 'rb') as f:
        data = bytearray(f.read())
    
    target = b'Nuevo   '
    replacement = b'New Game'
    
    idx = data.find(target)
    if idx != -1:
        data[idx:idx+len(target)] = replacement
        with open(path, 'wb') as f:
            f.write(data)
        print("Reverted level1 successfully on G drive!")
    else:
        print("Target not found on G drive!")

if __name__ == '__main__':
    unpatch_level_g()
