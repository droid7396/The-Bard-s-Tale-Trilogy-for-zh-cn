import UnityPy
import sys

def main():
    path = r"G:\SteamLibrary\steamapps\common\The Bard's Tale Trilogy\TheBardsTaleTrilogy_Data\sharedassets1.assets"
    env = UnityPy.load(path)
    types = set(obj.type.name for obj in env.objects)
    print('\n'.join(types))

if __name__ == '__main__':
    main()
