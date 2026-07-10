import urllib.request
import re
import os
import zipfile

url = "https://builds.bepinex.dev/projects/bepinex_be"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
except Exception as e:
    print("Failed to fetch:", e)
    exit(1)

# Find the latest build link
# href="/projects/bepinex_be/674/BepInEx-Unity.IL2CPP-win-x64-6.0.0-be.674%2Bf22e865.zip"
match = re.search(r'href="(/projects/bepinex_be/[0-9]+/BepInEx-Unity\.IL2CPP-win-x64-[^"]+\.zip)"', html)
if match:
    download_url = "https://builds.bepinex.dev" + match.group(1)
    print("Downloading:", download_url)
    zip_path = "bepinex_latest.zip"
    dl_req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(dl_req) as response, open(zip_path, 'wb') as out_file:
        out_file.write(response.read())
    print("Extracting...")
    game_dir = r"from Steam"
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(game_dir)
    os.remove(zip_path)
    print("Done")
else:
    print("Could not find download link")
