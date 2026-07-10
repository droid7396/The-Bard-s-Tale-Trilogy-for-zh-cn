# The Bard's Tale Trilogy 繁體中文化專案指南 (GEMINI.md)

這份文件記錄了從專案開始到目前為止的所有核心技術、外掛架構與工作流程。如果未來開啟了新的 AI 對話 Session，請讓 AI 優先閱讀此份文件，以確保無縫接軌。

---

## 1. 專案背景與技術難點

*   **遊戲引擎**：Unity (IL2CPP 架構)。
*   **字型系統**：使用了高度客製化的 `TextMeshPro` 元件。
*   **遭遇問題**：
    *   **AutoTranslator 失敗**：因為遊戲的 TextMeshPro 版本特殊，常見的 XUnity.AutoTranslator 無法成功 Hook 文字，且無法正確替換支援中文的字型，導致遊戲直接閃退或出現空白方塊。
    *   **直接修改 Asset 失敗**：因為中文字元 (UTF-8) 佔用的位元組數量與原本的英文字元不同，直接修改二進位檔案會破壞檔案偏移量 (Offset)，導致遊戲崩潰。

---

## 2. 解決方案：自製 ZHLocalizer 外掛

為了解決上述問題，我們放棄了現成的工具，轉而**完全自製了一套 BepInEx IL2CPP C# 外掛 (`ZHLocalizer`)**。

### 核心功能與黑科技
1.  **動態文字攔截 (Harmony Hook)**：
    外掛攔截了 `TMPro.TMP_Text.text` 的 `Setter` 方法。當遊戲試圖把英文顯示到畫面上時，外掛會搶先一步將其替換為中文。
2.  **動態字型注入 (Font Injection)**：
    將支援中文的字型打包成了 Unity AssetBundle (`arialuni_sdf_u2018`)。當外掛第一次攔截到需要翻譯的文字時，會自動讀取這個字型包，並將畫面上的字型強制替換為支援中文的字型，徹底解決「出現三個空白框」的問題。
3.  **動態變數自動對應 (Regex Formatting)**：
    支援帶有變數的翻譯（例如：`Level {0} Spells`）。外掛會在背景自動將其編譯為正規表示式 (Regex)。您在翻譯時可以隨意調換變數順序（例如：`{1} 被 {0} 打了`），外掛都能精準捕捉變數並正確替換。
4.  **容錯正規化引擎 (Normalization)**：
    外掛在比對英文字串時，會自動忽略所有的「隱形半形空白鍵」、「多餘的換行字元 (`\n`, `\r`)」等。這代表您在翻譯長篇故事時，不用再痛苦地對齊每一個空白鍵，只要文字內容正確，外掛就能配對成功！

---

## 3. 外掛程式的位置與修改方式

*   **專案位置**：`d:\git\The Bard's Tale Trilogy for zh\ZHLocalizer\`
*   **核心程式碼**：`Plugin.cs`
*   **如何修改與編譯**：
    1.  開啟終端機，切換到外掛資料夾：`cd "d:\git\The Bard's Tale Trilogy for zh\ZHLocalizer"`
    2.  如果您修改了 `Plugin.cs`，請執行編譯指令：`dotnet build`
    3.  編譯成功後，將新產生的 DLL 檔複製到遊戲目錄：
        ```powershell
        Copy-Item "bin\Debug\netstandard2.1\ZHLocalizer.dll" -Destination "G:\SteamLibrary\steamapps\common\The Bard's Tale Trilogy\BepInEx\plugins\" -Force
        ```

---

## 4. 日常翻譯工作流程 (Workflow)

我們撰寫了兩支 Python 工具來協助您處理龐大的文本：

### 步驟一：提取文本到 CSV (如果遊戲更新才需要)
*   **腳本**：`extract_to_csv.py`
*   **功能**：掃描遊戲解包出來的 `sharedassets0.assets_btr_localization.xml.txt`，智慧去除 `@@` 標籤，並將需要翻譯的英文部分匯出為 `Translation_Tasks.csv`。

### 步驟二：在 Excel 中進行翻譯 (主要工作)
1.  使用 Excel 開啟 `Translation_Tasks.csv`。
2.  在 `Chinese` 欄位填寫您的翻譯。
3.  **排版技巧**：遇到超長篇幅的故事（如 `CHAPTERSTORY_0`），請直接在同一個儲存格內進行翻譯。需要換行時，請按下 **`Alt + Enter`** 製造真實的換行，讓排版看起來舒服。**千萬不要手動輸入 `\n`。**
4.  翻譯完成後，存檔並關閉 Excel。

### 步驟三：將 CSV 轉換為外掛專用字典檔
*   **腳本**：`csv_to_zh_dict.py`
*   **執行方式**：在終端機輸入 `python csv_to_zh_dict.py`
*   **功能與魔法**：
    它會讀取您剛剛存檔的 CSV。最重要的是，它會**自動將您在 Excel 裡用 `Alt+Enter` 產生的真實換行，全部轉換成字串 `\n`**。這樣一來，長篇文章就能完美濃縮成「單行格式」，符合 BepInEx 外掛 `zh_translations.txt` 的讀取規範。
*   轉換成功後，您會得到一個更新版的 `zh_translations.txt`。

### 步驟四：套用到遊戲中
將產生的 `zh_translations.txt` 複製並覆蓋到以下路徑：
`G:\SteamLibrary\steamapps\common\The Bard's Tale Trilogy\BepInEx\plugins\zh_translations.txt`
（同時確保字型檔 `arialuni_sdf_u2018` 也在同一個資料夾下）。

打開遊戲，享受您的漢化成果！

---

## 5. 模組發布方式 (Release)

當翻譯全部完成後，可以透過打包工具產生 ZIP 檔給其他玩家使用。

### 準備打包的檔案結構：
`	ext
TheBardsTaleTrilogy_ZH_Mod.zip
├── BepInEx/                    (BepInEx 框架資料夾)
│   ├── core/                   (框架核心檔)
│   └── plugins/                (外掛資料夾)
│       ├── ZHLocalizer.dll     (攔截外掛程式)
│       ├── arialuni_sdf_u2018  (中文字型檔)
│       └── zh_translations.txt (您翻譯的字典檔)
├── dotnet/                     (BepInEx 依賴的執行環境)
├── doorstop_config.ini         (BepInEx 啟動設定檔)
└── winhttp.dll                 (啟動時劫持遊戲的 DLL)
`
**注意：絕對不可以打包 BepInEx/interop 或 BepInEx/cache 資料夾**，因為這些是根據玩家電腦即時產生的快取檔案，容量極大且每台電腦不同。

### 發支給玩家的 Readme 提醒事項：
*   **安裝方式**：解壓縮後將所有檔案覆蓋至遊戲根目錄（TheBardsTaleTrilogy.exe 所在位置）。
*   **首次啟動黑屏**：因為這是 IL2CPP 架構遊戲，**首次啟動時畫面可能會黑屏 1 到 3 分鐘**（遊戲正在背景自動產生 interop 快取檔案）。請務必提醒玩家耐心等待，千萬不要強制關閉遊戲。

### 一鍵打包工具
*   **腳本**：uild_release.py
*   **功能**：自動前往遊戲安裝目錄抓取必要的檔案（且自動排除不需要的巨大快取資料夾），並在目前專案目錄下產生乾淨的發布壓縮檔 TheBardsTaleTrilogy_ZH_Mod.zip。
