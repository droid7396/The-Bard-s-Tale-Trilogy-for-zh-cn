import os
import UnityPy

data_dir = r'from Steam\TheBardsTaleTrilogy_Data'
files = [f for f in os.listdir(data_dir) if f.endswith('.assets') or f == 'globalgamemanagers']
fonts = []

for root, dirs, files_list in os.walk(data_dir):
    for f in files_list:
        if f.endswith('.assets') or f.startswith('level') or f.endswith('.resource') or f == 'globalgamemanagers':
            file_path = os.path.join(root, f)
            try:
                env = UnityPy.load(file_path)
                for obj in env.objects:
                    if obj.type.name in ('Font', 'TMP_FontAsset', 'TextMeshProFont'):
                        data = obj.read()
                        fonts.append((f, obj.type.name, getattr(data, 'name', 'unnamed')))
            except Exception as e:
                pass

print('Fonts found:')
for font in set(fonts):
    print(font)
