# The Bard's Tale Trilogy - 繁體中文化專案 (ZHLocalizer)

這是一個專為《冰城傳奇三部曲》(The Bard's Tale Trilogy) 打造的繁體中文化開源專案。

因為遊戲底層架構的特殊性，傳統的翻譯工具無法起作用，因此本專案從零開始建立了一套基於 BepInEx 的動態文字替換外掛 (`ZHLocalizer`)，並搭配 Python 自動化腳本，達成完美的繁體中文化。

---

## 🏗️ 技術基礎與挑戰

本遊戲採用 **Unity (IL2CPP)** 架構，且文字渲染使用了高度客製化的 `TextMeshPro` 元件。

在專案初期，我們嘗試過現成的 XUnity.AutoTranslator，但面臨了以下無法克服的困難：
1. **無法 Hook 文字**：AutoTranslator 無法成功攔截此遊戲特製版本的 TextMeshPro 文字。
2. **字型顯示異常**：無法正確替換支援中文的字型，遊戲會直接閃退或文字變成「空白方塊」。
3. **二進位修改失敗**：中文字元佔用的位元組與英文不同，直接修改 Asset 檔會破壞檔案偏移量 (Offset) 導致崩潰。

---

## 🚀 專案發展與核心技術

為了解決上述難題，我們開發了專屬的 C# 外掛 **`ZHLocalizer`**。它具備以下「黑科技」：

*   **動態文字攔截 (Harmony Hook)**：
    攔截 `TMPro.TMP_Text.text` 的寫入，在遊戲將英文顯示到畫面前，搶先替換為中文。
*   **動態字型注入 (Font Injection)**：
    將支援中文的字型打包為 Unity AssetBundle (`arialuni_sdf_u2018`)。外掛會在背景自動載入，並強制替換畫面上的字型，徹底解決空白方塊問題。
*   **動態變數與正則表達式 (Regex)**：
    遊戲中有許多動態組合的句子（如 `Level {0} {1}`）。外掛內建正則化引擎，可以精準捕捉變數，並且支援「遞迴翻譯」（先翻譯變數，再組裝成長句翻譯）。
*   **容錯匹配引擎**：
    自動忽略原文中隱形的半形空白、多餘的換行字元 (`\n`, `\r`)，讓翻譯檔的維護更為輕鬆。

---

## 🏆 最後成果

透過本專案的技術，我們實現了：
1. **100% 介面與文本中文化**：從 UI 選單、道具到長篇故事，全部皆可完美翻譯。
2. **完美相容動態顏色標籤**：保留了遊戲原有的字體顏色（例如：`<color=#ffff22>A</color>dd member`），排版不跑位。
3. **支援中文輸入**：解決了玩家創建角色時輸入中文會變成亂碼的問題。現在輸入框能自動偵測中文字元並套用對應字型。
4. **Steam Deck 完美支援**：在 Proton 相容層下也可順利執行。

---

## 📦 封裝與開發工作流程

我們撰寫了一系列的 Python 工具來輔助翻譯與封裝作業：

### 1. 翻譯工作流
*   **`extract_to_csv.py`**：從遊戲解包的原始 XML 中，提取出需要翻譯的純英文文本，並匯出為 `Translation_Tasks.csv` 供翻譯人員（或 LLM）在 Excel 中作業。
*   **`llm_translate.py`**：透過串接 DeepSeek API 等大型語言模型，進行自動化批量翻譯。
*   **`csv_to_zh_dict.py`**：將翻譯好的 CSV 檔轉換為外掛專用的 `zh_translations.txt` 字典檔。會自動處理換行符號與格式轉換。

### 2. 編譯與發布
*   **`ZHLocalizer/Plugin.cs`**：使用 `dotnet build` 即可編譯產生 `ZHLocalizer.dll`。
*   **`build_release.py`**：一鍵打包發布工具。會自動前往遊戲安裝目錄抓取必要的框架檔案（並排除無用的巨大快取檔），最後生成給玩家安裝的 `TheBardsTaleTrilogy_ZH_Mod.zip`。

---

## 🎮 玩家使用方式

若您是純粹想遊玩中文化的玩家，請參考 [README_ZH_Mod.md](README_ZH_Mod.md) 中的安裝與使用說明。
