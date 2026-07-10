import csv
import os

def convert_csv_to_dict(csv_path, output_dict_path):
    if not os.path.exists(csv_path):
        print(f"找不到檔案：{csv_path}。請確保它存在同一個資料夾。")
        input("按 Enter 鍵離開...")
        return

    translations = []
    count = 0
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        next(reader) # skip header
        for row in reader:
            if len(row) >= 3:
                en_text = row[1].strip()
                zh_text = row[2].strip()
                # 只匯出有填寫中文翻譯的項目
                if zh_text:
                    # 將 Excel 中的真實換行轉換為 \n 字元，確保 Plugin.cs 能夠正確讀取同一行
                    en_text = en_text.replace('\r\n', '\\n').replace('\n', '\\n')
                    zh_text = zh_text.replace('\r\n', '\\n').replace('\n', '\\n')
                    translations.append(f"{en_text}={zh_text}\n")
                    count += 1

    if count > 0:
        with open(output_dict_path, 'w', encoding='utf-8') as f:
            f.writelines(translations)
        print(f"轉換成功！已將 {count} 筆翻譯匯出至 {output_dict_path}")
        print("請將產生的 zh_translations.txt 複製到遊戲的 BepInEx/plugins/ 資料夾下覆蓋原本的檔案。")
    else:
        print("CSV 檔案中尚未填寫任何中文翻譯 (Chinese 欄位為空)。沒有產生字典檔。")

    input("按 Enter 鍵離開...")

if __name__ == '__main__':
    convert_csv_to_dict("Translation_Tasks.csv", "zh_translations_new.txt")
