import os
import zipfile
import urllib.request
import re
import shutil
import tempfile

GAME_DIR = r"G:\SteamLibrary\steamapps\common\The Bard's Tale Trilogy"
OUTPUT_ZIP = "TheBardsTaleTrilogy_ZH_Mod_x86.zip"

def download_bepinex_x86(dest_dir):
    url = "https://builds.bepinex.dev/projects/bepinex_be"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print("無法取得 BepInEx 版本列表:", e)
        return False

    # 尋找最新的 win-x86 版本
    match = re.search(r'href="(/projects/bepinex_be/[0-9]+/BepInEx-Unity\.IL2CPP-win-x86-[^"]+\.zip)"', html)
    if match:
        download_url = "https://builds.bepinex.dev" + match.group(1)
        print("正在下載 32-bit BepInEx:", download_url)
        zip_path = os.path.join(dest_dir, "bepinex_x86.zip")
        dl_req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(dl_req) as response, open(zip_path, 'wb') as out_file:
            out_file.write(response.read())
        
        print("解壓縮 32-bit BepInEx...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
        os.remove(zip_path)
        return True
    else:
        print("找不到 32-bit BepInEx 的下載連結。")
        return False

def main():
    print(f"開始打包 32-bit 中文化模組: {OUTPUT_ZIP} ...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. 下載 x86 版 BepInEx
        if not download_bepinex_x86(temp_dir):
            return

        # 2. 準備打包的檔案 (來自遊戲目錄的外掛檔案)
        plugin_files = [
            "BepInEx/plugins/ZHLocalizer.dll",
            "BepInEx/plugins/arialuni_sdf_u2018",
            "BepInEx/plugins/btr_localization_zh.txt",
            "BepInEx/plugins/combat_translations.txt",
        ]
        
        # 將外掛檔案複製到 temp_dir
        for item in plugin_files:
            src_path = os.path.join(GAME_DIR, item)
            dst_path = os.path.join(temp_dir, item)
            
            if not os.path.exists(src_path):
                print(f"警告: 找不到檔案 {src_path}，將跳過。")
                continue
                
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src_path, dst_path)
            print(f"已複製外掛檔案: {item}")

        # 3. 將 temp_dir 中的所有內容打包成 ZIP
        with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, temp_dir)
                    zipf.write(full_path, rel_path)
                    
    print(f"\n打包完成！您已成功建立 32-bit 發布檔案：{OUTPUT_ZIP}")
    print("您可以將此 ZIP 檔發布給 32-bit 系統的玩家。")

if __name__ == "__main__":
    main()
