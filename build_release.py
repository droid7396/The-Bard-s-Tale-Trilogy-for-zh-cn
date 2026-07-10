import os
import zipfile

# 遊戲安裝目錄
GAME_DIR = r"G:\SteamLibrary\steamapps\common\The Bard's Tale Trilogy"
# 輸出的 ZIP 檔名
OUTPUT_ZIP = "TheBardsTaleTrilogy_ZH_Mod.zip"

def main():
    print(f"開始打包中文化模組: {OUTPUT_ZIP} ...")
    
    # 需要打包的檔案或資料夾名單 (相對於遊戲目錄)
    # 若是資料夾，則會打包其底下所有內容
    files_to_pack = [
        "doorstop_config.ini",
        "winhttp.dll",
        "dotnet",         # 資料夾
        "BepInEx/core",   # 資料夾
        "BepInEx/plugins/ZHLocalizer.dll",
        "BepInEx/plugins/arialuni_sdf_u2018",
        "BepInEx/plugins/zh_translations.txt",
    ]
    
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in files_to_pack:
            item_path = os.path.join(GAME_DIR, item)
            
            if not os.path.exists(item_path):
                print(f"警告: 找不到檔案或資料夾 {item_path}，跳過。")
                continue
                
            if os.path.isfile(item_path):
                print(f"加入檔案: {item}")
                zipf.write(item_path, item)
            elif os.path.isdir(item_path):
                for root, dirs, files in os.walk(item_path):
                    for file in files:
                        full_path = os.path.join(root, file)
                        # 計算在 ZIP 中的相對路徑
                        rel_path = os.path.relpath(full_path, GAME_DIR)
                        zipf.write(full_path, rel_path)
                print(f"加入資料夾: {item}")
                
    print(f"\n打包完成！您已成功建立發布檔案：{OUTPUT_ZIP}")
    print("您可以將此 ZIP 檔發布給其他玩家。")
    print("請務必在發布網頁提醒玩家：首次進入遊戲會黑屏 1~3 分鐘建立快取，屬正常現象。")

if __name__ == "__main__":
    main()
