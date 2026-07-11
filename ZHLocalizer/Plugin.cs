using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using BepInEx;
using BepInEx.Unity.IL2CPP;
using UnityEngine;
using HarmonyLib;
using TMPro;

namespace ZHLocalizer
{
    [BepInPlugin("com.antigravity.zhlocalizer", "ZH Localizer", "1.0.0")]
    public class Plugin : BasePlugin
    {
        public static Dictionary<string, string> Translations = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        public static Dictionary<Regex, string> RegexTranslations = new Dictionary<Regex, string>();
        public static Dictionary<string, string> TranslationCache = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        public static BepInEx.Logging.ManualLogSource Logger;

        public static string NormalizeText(string input)
        {
            if (string.IsNullOrEmpty(input)) return input;
            // Replace all whitespace sequences (including spaces, tabs, newlines) with a single space
            return Regex.Replace(input, @"\s+", " ").Trim();
        }

        public override void Load()
        {
            Logger = Log;
            Logger.LogInfo("ZHLocalizer Plugin Loaded!");
            
            // Load translations
            string dictPath = Path.Combine(Paths.PluginPath, "zh_translations.txt");
            try
            {
                if (File.Exists(dictPath))
                {
                    foreach (string line in File.ReadAllLines(dictPath))
                    {
                        if (string.IsNullOrWhiteSpace(line) || line.StartsWith("#")) continue;
                        var parts = line.Split(new[] { "=ZH=" }, 2, StringSplitOptions.None);
                        if (parts.Length == 2)
                        {
                            string key = parts[0].Trim().Replace("\\n", "\n");
                            string val = parts[1].Trim().Replace("\\n", "\n");
                            
                            if (Regex.IsMatch(key, @"\{\d+\}"))
                            {
                                // 避免 {0} 或 {2} 這種純變數的翻譯變成 match all 的 regex
                                string cleanKey = Regex.Replace(key, @"\{\d+\}", "").Trim();
                                if (string.IsNullOrEmpty(cleanKey))
                                {
                                    continue; // 純變數沒有翻譯的意義，直接略過
                                }

                                if (key == val) continue; // Skip entries where translation is identical to original

                                try
                                {
                                    string pattern = Regex.Escape(NormalizeText(key));
                                    // Regex.Escape in .NET Standard 2.1/Core might not escape braces { and }.
                                    // So we match optionally escaped braces. Add 'g' prefix because .NET group names cannot be '0'
                                // 最後一組用貪心匹配，其餘用非貪心
                                int groupCount = Regex.Matches(key, @"\{\d+\}").Count;
                                int currentGroupIndex = 0;
                                pattern = Regex.Replace(pattern, @"\\?\{(\d+)\\?\}", m => {
                                    currentGroupIndex++;
                                    bool isLast = (currentGroupIndex == groupCount);
                                    return isLast ? "(?<g" + m.Groups[1].Value + ">.+)" : "(?<g" + m.Groups[1].Value + ">.+?)";
                                });
                                    pattern = "^" + pattern + "$";
                                    Regex regex = new Regex(pattern, RegexOptions.IgnoreCase);
                                    RegexTranslations[regex] = val;
                                }
                                catch (Exception ex)
                                {
                                    Logger.LogError("Failed to compile regex for: " + key + " Error: " + ex);
                                }
                            }
                            else
                            {
                                Translations[NormalizeText(key)] = val;
                            }
                        }
                    }
                    Logger.LogInfo($"Loaded {Translations.Count} exact translations and {RegexTranslations.Count} dynamic format translations.");
                }
                else
                {
                    File.WriteAllText(dictPath, "New Game=新遊戲\nLoad Game=載入遊戲\nOptions=選項\nQuit Game=離開遊戲\nLevel {0} Spells=第 {0} 級法術\n");
                    Logger.LogInfo("Created dummy zh_translations.txt");
                }
            }
            catch (Exception ex)
            {
                Logger.LogError("Failed to load zh_translations.txt: " + ex);
            }

            // Apply Harmony patches
            Harmony.CreateAndPatchAll(typeof(Hooks));

            // 新增：起動周期性文字掃描器 (專門處理未進入 Harmony Hook 的 Tooltip UI)
            AddComponent<TextScannerBehaviour>();

            // RUN A DIAGNOSTIC TEST
            string testStr = "Press <color=#ffff22>SPACE</color> to continue...";
            string normTest = NormalizeText(testStr);
            Plugin.Logger.LogInfo("=== DIAGNOSTIC TEST ===");
            Plugin.Logger.LogInfo("Testing string: " + normTest);
            foreach (var kvp in RegexTranslations)
            {
                if (kvp.Key.ToString().StartsWith("^Press", StringComparison.OrdinalIgnoreCase))
                {
                    Plugin.Logger.LogInfo("Comparing against regex: " + kvp.Key.ToString());
                    Match m = kvp.Key.Match(normTest);
                    Plugin.Logger.LogInfo("Match success: " + m.Success);
                }
            }
            Plugin.Logger.LogInfo("TranslateString result: " + (Hooks.TranslateString(testStr) ?? "NULL"));
            
            // DIAGNOSTIC FOR LV
            foreach (var kvp in RegexTranslations)
            {
                if (kvp.Key.ToString().Contains("Lv"))
                {
                    Plugin.Logger.LogInfo("FOUND LV REGEX: " + kvp.Key.ToString() + " => " + kvp.Value);
                }
            }

            Plugin.Logger.LogInfo("=== END DIAGNOSTIC ===");
        }
    }

    // ==========================================================
    // 周期性文字掃描器 - 掃描全場景 (包含 DontDestroyOnLoad) 來處理 Tooltip
    // ==========================================================
    public class TextScannerBehaviour : MonoBehaviour
    {
        private float _timer = 0f;
        private const float SCAN_INTERVAL = 0.15f;
        private readonly Dictionary<int, int> _seen = new Dictionary<int, int>();
        private UnityEngine.SceneManagement.Scene _dontDestroyOnLoadScene;
        private bool _hasDontDestroyScene = false;

        void Start()
        {
            // 取得 DontDestroyOnLoad 場景的標準做法：創一個暫時物件移過去，然後取得它的 scene
            GameObject temp = new GameObject("TempForDontDestroyOnLoad");
            DontDestroyOnLoad(temp);
            _dontDestroyOnLoadScene = temp.scene;
            _hasDontDestroyScene = true;
            Destroy(temp);
        }

        void Update()
        {
            _timer += Time.deltaTime;
            if (_timer < SCAN_INTERVAL) return;
            _timer = 0f;
            if (Hooks.ChineseFont == null) return;
            
            try 
            { 
                var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
                if (scene.IsValid() && scene.isLoaded)
                {
                    foreach (var go in scene.GetRootGameObjects())
                        ScanGO(go);
                }

                if (_hasDontDestroyScene && _dontDestroyOnLoadScene.IsValid())
                {
                    foreach (var go in _dontDestroyOnLoadScene.GetRootGameObjects())
                        ScanGO(go);
                }

                if (_seen.Count > 10000) _seen.Clear();
            } 
            catch { }
        }

        private void ScanGO(GameObject go)
        {
            if (go == null || !go.activeInHierarchy) return;
            
            var tmp = go.GetComponent<TMP_Text>();
            if (tmp != null && !string.IsNullOrEmpty(tmp.text))
            {
                int id = tmp.GetInstanceID();
                int hash = tmp.text.GetHashCode();

                if (!_seen.TryGetValue(id, out int prev) || prev != hash)
                {
                    if (Regex.IsMatch(tmp.text, @"[a-zA-Z]{3}"))
                    {
                        string t = tmp.text;
                        Hooks.TMP_Text_set_text_Prefix(ref t, tmp);
                        if (t != tmp.text) tmp.SetText(t);
                    }
                    _seen[id] = tmp.text.GetHashCode();
                }
            }

            // 同時掃描標準的 UnityEngine.UI.Text (防具有可能是用這個)
            var stdText = go.GetComponent<UnityEngine.UI.Text>();
            if (stdText != null && !string.IsNullOrEmpty(stdText.text))
            {
                int id = stdText.GetInstanceID();
                int hash = stdText.text.GetHashCode();

                if (!_seen.TryGetValue(id, out int prev) || prev != hash)
                {
                    if (Regex.IsMatch(stdText.text, @"[a-zA-Z]{3}"))
                    {
                        string t = stdText.text;
                        // 借用 Hooks 裡的邏輯，但不用中文字型處理，純翻譯
                        string translated = Hooks.TranslateString(t);
                        if (!string.IsNullOrEmpty(translated) && translated != stdText.text)
                        {
                            stdText.text = translated;
                        }
                        else if (t.Contains("TRZP") || t.Contains("This spell"))
                        {
                            Plugin.Logger.LogWarning("[DEBUG] TextScanner Failed: '" + t.Replace("\n", "\\n").Replace("\r", "\\r") + "'");
                        }
                    }
                    _seen[id] = stdText.text.GetHashCode();
                }
            }

            for (int i = 0; i < go.transform.childCount; i++)
            {
                var child = go.transform.GetChild(i);
                if (child != null) ScanGO(child.gameObject);
            }
        }
    }

    public class Hooks
    {
        public static TMP_FontAsset ChineseFont = null;
        public static bool FontLoaded = false;
        public static Dictionary<int, Material> MaterialCache = new Dictionary<int, Material>();
        public static Dictionary<int, TMP_Text> TrackedTexts = new Dictionary<int, TMP_Text>();

        public static string TranslateString(string input)
        {
            if (string.IsNullOrEmpty(input)) return null;
            string normalizedValue = Plugin.NormalizeText(input);

            if (Plugin.Translations.TryGetValue(normalizedValue, out string translated))
            {
                return translated;
            }
            if (Plugin.TranslationCache.TryGetValue(normalizedValue, out translated))
            {
                return translated;
            }
            foreach (var kvp in Plugin.RegexTranslations)
            {
                Match m = kvp.Key.Match(normalizedValue);
                if (m.Success)
                {
                    if (normalizedValue.Contains("This spell") || normalizedValue.Contains("Conjurer: 0"))
                    {
                        Plugin.Logger.LogWarning($"[DEBUG] Matched Regex: '{kvp.Key}' (Value: '{kvp.Value}') for string: '{normalizedValue}'");
                    }
                    string result = kvp.Value;
                    bool anyGroupTranslated = false;
                    foreach (Group group in m.Groups)
                    {
                        if (group.Name.StartsWith("g") && int.TryParse(group.Name.Substring(1), out _))
                        {
                            string groupVal = group.Value;
                            string groupTranslated = null;
                            string norm = Plugin.NormalizeText(groupVal);
                            
                            // Strip tags for lookup so e.g. <color>Conjurer</color> translates properly
                            string strippedNorm = Regex.Replace(norm, @"<[^>]*>", "");
                            // 遞迴翻譯：先嘗試直接查表，再遞迴呼叫 TranslateString (支援長文、Regex配對)
                            if (Plugin.Translations.TryGetValue(strippedNorm, out string t) || Plugin.TranslationCache.TryGetValue(strippedNorm, out t))
                            {
                                Match tagsStart = Regex.Match(norm, @"^(?:<[^>]*>)+");
                                Match tagsEnd = Regex.Match(norm, @"(?:<[^>]*>)+$");
                                groupTranslated = tagsStart.Value + t + tagsEnd.Value;
                                anyGroupTranslated = true;
                            }
                            else
                            {
                                // 遞迴呼叫 TranslateString 自身，支援含有換行、多句的長文說明
                                string recursiveResult = TranslateString(groupVal);
                                if (recursiveResult != null)
                                {
                                    groupTranslated = recursiveResult;
                                    anyGroupTranslated = true;
                                }
                            }
                            
                            if (groupTranslated == null && groupVal.Contains("This spell"))
                            {
                                Plugin.Logger.LogWarning("[DEBUG] Regex Group Failed Translate: '" + strippedNorm + "'");
                            }

                            result = result.Replace("{" + group.Name.Substring(1) + "}", groupTranslated ?? groupVal);
                        }
                    }

                    Plugin.TranslationCache[normalizedValue] = result;
                    return result;
                }
            }
            return null;
        }

        [HarmonyPatch(typeof(TMP_Text), nameof(TMP_Text.text), MethodType.Setter)]
        [HarmonyPrefix]
        public static void TMP_Text_set_text_Prefix(ref string value, TMP_Text __instance)
        {
            if (string.IsNullOrEmpty(value)) return;

            // 印出最原始的字串，方便查修
            if (value.Contains("Conjurer") || value.Contains("Robes"))
            {
                Plugin.Logger.LogWarning("[DEBUG] ORIGINAL STRING: " + value.Replace("\n", "\\n"));
            }

            // Strip font and material tags to prevent texture atlas mismatch on hover
            value = Regex.Replace(value, @"<font[^>]*>", "", RegexOptions.IgnoreCase);
            value = Regex.Replace(value, @"</font>", "", RegexOptions.IgnoreCase);
            value = Regex.Replace(value, @"<material[^>]*>", "", RegexOptions.IgnoreCase);
            value = Regex.Replace(value, @"</material>", "", RegexOptions.IgnoreCase);

            bool isTranslated = false;
            
            string translatedResult = TranslateString(value);
            if (translatedResult != null)
            {
                value = translatedResult;
                isTranslated = true;
            }
            // 處理遊戲使用 TMP_Text.text += "新句子" 的情況
            else if (!string.IsNullOrEmpty(__instance.text) && value.StartsWith(__instance.text))
            {
                string appended = value.Substring(__instance.text.Length);
                string trimmedAppended = appended.TrimStart();
                string leadingWhitespace = appended.Substring(0, appended.Length - trimmedAppended.Length);
                
                string translatedAppended = TranslateString(trimmedAppended);
                if (translatedAppended != null)
                {
                    value = __instance.text + leadingWhitespace + translatedAppended;
                    isTranslated = true;
                }
            }

            // 新增：如果整句沒有配對成功，嘗試去除頭尾的排版標籤 (例如 <color> 或 <b>) 再配對
            if (!isTranslated)
            {
                string leadingTags = "";
                string trailingTags = "";
                string coreValue = value;

                Match mStart = Regex.Match(coreValue, @"^(?:<color=[^>]*>|<align=[^>]*>|<b>|<i>|<size=[^>]*>)+", RegexOptions.IgnoreCase);
                if (mStart.Success)
                {
                    leadingTags = mStart.Value;
                    coreValue = coreValue.Substring(mStart.Length);
                }
                Match mEnd = Regex.Match(coreValue, @"(?:</color>|</align>|</b>|</i>|</size>)+$", RegexOptions.IgnoreCase);
                if (mEnd.Success)
                {
                    trailingTags = mEnd.Value;
                    coreValue = coreValue.Substring(0, coreValue.Length - mEnd.Length);
                }

                if (coreValue != value)
                {
                    string t = TranslateString(coreValue);
                    if (t != null)
                    {
                        value = leadingTags + t + trailingTags;
                        isTranslated = true;
                    }
                }
            }

            // 新增：針對未標籤化的短名詞 (例如 "Male Gnome Conjurer") 進行逐字翻譯嘗試
            if (!isTranslated && !value.Contains("<"))
            {
                string[] words = value.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                if (words.Length >= 2 && words.Length <= 5)
                {
                    bool allTranslated = true;
                    string combined = "";
                    foreach (var w in words)
                    {
                        string tw = TranslateString(w);
                        if (tw != null) combined += tw;
                        else { allTranslated = false; break; }
                    }
                    if (allTranslated)
                    {
                        value = combined;
                        isTranslated = true;
                    }
                }
            }

            // ==========================================
            // 強制硬替換 (防呆機制) - 確保這些 Tooltip 絕對能被翻譯
            // ==========================================
            bool fallbackTriggered = false;
            if (!isTranslated)
            {
                // 法術 Tooltip 防呆替換
                if (value.Contains("Conjurer Lv") || value.Contains("Magician Lv") || value.Contains("Sorcerer Lv") || value.Contains("Wizard Lv"))
                {
                    value = value.Replace("MAFL", "法力微光");
                    value = value.Replace("ARFI", "秘法火焰");
                    value = value.Replace("TRZP", "陷阱解除");
                    value = value.Replace("SOSH", "術士護盾");
                    value = value.Replace("Conjurer", "咒術師");
                    value = value.Replace("Magician", "魔術師");
                    value = value.Replace("Sorcerer", "術士");
                    value = value.Replace("Wizard", "巫師");
                    value = Regex.Replace(value, @"\s*Lv\s*", " 等級 ");
                    fallbackTriggered = true;
                }

                // 道具 Tooltip 防呆替換
                if (value.Contains("Slot:"))
                {
                    // 嘗試翻譯 Equipped 後面的裝備名稱
                    Match mEquipped = Regex.Match(value, @"Equipped:\s*([^\n\r]+)");
                    if (mEquipped.Success)
                    {
                        string eqName = mEquipped.Groups[1].Value.Trim();
                        string eqTrans = TranslateString(eqName);
                        if (eqTrans != null)
                        {
                            value = value.Replace("Equipped: " + eqName, "已裝備：" + eqTrans);
                            value = value.Replace("Equipped:" + eqName, "已裝備：" + eqTrans);
                        }
                    }

                    value = value.Replace("Slot: ", "欄位：");
                    value = value.Replace("Slot:", "欄位：");
                    value = value.Replace("Weapon", "武器");
                    value = value.Replace("Armor", "防具");
                    value = value.Replace("Equipped: ", "已裝備：");
                    value = value.Replace("Equipped:", "已裝備：");
                    value = value.Replace("Damage Min:", "最小傷害：");
                    value = value.Replace("Damage Max:", "最大傷害：");
                    value = value.Replace("Classes: All Classes", "適用職業：所有職業");
                    fallbackTriggered = true;
                }
            }

            // 新增：如果還是沒有配對成功，且字串包含多行，嘗試按行切開分別翻譯
            bool anyLineTranslated = false;
            if (!isTranslated && value.Contains("\n"))
            {
                string[] lines = value.Split(new[] { "\r\n", "\n" }, StringSplitOptions.None);

                for (int i = 0; i < lines.Length; i++)
                {
                    string line = lines[i];
                    if (string.IsNullOrWhiteSpace(line)) continue;
                    string coreLine = line.Trim();

                    // 對單行也嘗試去除頭尾標籤
                    string leadingTagsLine = "";
                    string trailingTagsLine = "";
                    string coreValueLine = coreLine;

                    Match mStartLine = Regex.Match(coreValueLine, @"^(?:<color=[^>]*>|<align=[^>]*>|<b>|<i>|<size=[^>]*>)+", RegexOptions.IgnoreCase);
                    if (mStartLine.Success)
                    {
                        leadingTagsLine = mStartLine.Value;
                        coreValueLine = coreValueLine.Substring(mStartLine.Length);
                    }
                    Match mEndLine = Regex.Match(coreValueLine, @"(?:</color>|</align>|</b>|</i>|</size>)+$", RegexOptions.IgnoreCase);
                    if (mEndLine.Success)
                    {
                        trailingTagsLine = mEndLine.Value;
                        coreValueLine = coreValueLine.Substring(0, coreValueLine.Length - mEndLine.Length);
                    }

                    if (coreValueLine != coreLine)
                    {
                        string tCore = TranslateString(coreValueLine);
                        if (tCore != null)
                        {
                            lines[i] = leadingTagsLine + tCore + trailingTagsLine;
                            anyLineTranslated = true;
                        }
                        else 
                        {
                            // 針對 Tooltip 中類似 "Conjurer Lv 1" 或 "Magician Lv 1" 進行特殊處理
                            Match mLv = Regex.Match(coreValueLine, @"^\s*(Conjurer|Magician|Sorcerer|Wizard|咒術師|魔術師|術士|巫師)\s*(?:Lv|等級)\s*(\d+)\s*$");
                            if (mLv.Success)
                            {
                                string className = mLv.Groups[1].Value;
                                string transClass = className == "Conjurer" ? "咒術師" :
                                                    className == "Magician" ? "魔術師" :
                                                    className == "Sorcerer" ? "術士" :
                                                    className == "Wizard" ? "巫師" : className;
                                lines[i] = leadingTagsLine + transClass + " 等級 " + mLv.Groups[2].Value + trailingTagsLine;
                                anyLineTranslated = true;
                            }
                        }
                    }
                    else
                    {
                        string tLine = TranslateString(coreLine);
                        if (tLine != null)
                        {
                            lines[i] = tLine;
                            anyLineTranslated = true;
                        }
                    }
                }

                if (anyLineTranslated)
                {
                    value = string.Join("\n", lines);
                    isTranslated = true;
                }
            }

            if (fallbackTriggered)
            {
                isTranslated = true;
            }

            bool hasChineseChars = Regex.IsMatch(value, @"\p{IsCJKUnifiedIdeographs}");
            
            // ==========================================
            // 特殊排版修正 (硬解 UI 跑版問題)
            // ==========================================
            if (isTranslated || hasChineseChars)
            {
                // 1. 人物屬性表 (Stats Screen)
                if (value.Contains("經驗值") && value.Contains("力量") && value.Contains("智力"))
                {
                    // 將「角色描述（性別種族職業）」與「等級：X」分開，讓名稱獨立一行
                    value = Regex.Replace(value, @"([\u4e00-\u9fff])\s*等級[:：]", "$1\n等級：");
                    value = Regex.Replace(value, @"\s*經驗值[:：]", "   經驗值：");
                    value = Regex.Replace(value, @"\s*力量[:：]", "\n力量：");
                    value = Regex.Replace(value, @"\s*智力[:：]", "   智力：");
                    value = Regex.Replace(value, @"\s*敏捷[:：]", "\n敏捷：");
                    value = Regex.Replace(value, @"\s*體質[:：]", "   體質：");
                    value = Regex.Replace(value, @"\s*(運氣|幸運)[:：]", "\n$1：");
                    value = Regex.Replace(value, @"\s*生命值[:：]", "   生命值：");
                    value = Regex.Replace(value, @"\s*法力值[:：]", "\n法力值：");
                    value = Regex.Replace(value, @"\s*近戰傷害[:：]", "   近戰傷害：");
                }
                
                // 2. 施法者等級表 (Caster levels)
                if (Regex.IsMatch(value, @"(魔術師|咒術師)[:：]\s*\d+") && Regex.IsMatch(value, @"(魔法師|法師)[:：]\s*\d+"))
                {
                    value = Regex.Replace(value, @"\s*(魔法師|法師)[:：]", "   $1：");
                    value = Regex.Replace(value, @"\s*(術士|巫師)[:：]", "   $1：");
                    value = Regex.Replace(value, @"(\d+)(巫師|術士)[:：]", "$1   $2：");
                }
            }
            
            if (isTranslated || hasChineseChars)
            {
                if (!value.StartsWith("<line-height="))
                {
                    value = "<line-height=130%>" + value;
                }

                if (!FontLoaded)
                {
                    FontLoaded = true;
                    try
                    {
                        string bundlePath = Path.Combine(Paths.PluginPath, "arialuni_sdf_u2018");
                        if (File.Exists(bundlePath))
                        {
                            var bundle = AssetBundle.LoadFromFile(bundlePath);
                            if (bundle != null)
                            {
                                var obj = bundle.LoadAsset("ARIALUNI SDF");
                                ChineseFont = obj.Cast<TMP_FontAsset>();
                                Plugin.Logger.LogInfo("Successfully loaded Chinese Font Asset!");
                            }
                        }
                        else
                        {
                            Plugin.Logger.LogError("Font bundle not found at: " + bundlePath);
                        }
                    }
                    catch (Exception ex)
                    {
                        Plugin.Logger.LogError("Failed to load font bundle: " + ex);
                    }
                }

                if (ChineseFont != null)
                {
                    __instance.font = ChineseFont;
                }
            }
            else
            {
                // 如果沒有被翻譯，印出來看看原文到底長怎樣，方便抓漏
                if (value.Length > 2)
                {
                    if (value.Contains("TRZP") || value.Contains("This spell"))
                    {
                        Plugin.Logger.LogWarning("[DEBUG] UNTRANSLATED TRZP: '" + value.Replace("\n", "\\n").Replace("\r", "\\r") + "'");
                        Plugin.Logger.LogWarning("[DEBUG] Normalized TRZP: '" + Plugin.NormalizeText(value) + "'");
                    }
                    Plugin.Logger.LogWarning("Untranslated: " + value);
                }
            }
        }

        [HarmonyPatch(typeof(TMP_Text), "fontSharedMaterial", MethodType.Setter)]
        [HarmonyPrefix]
        public static void TMP_Text_set_fontSharedMaterial_Prefix(ref Material value, TMP_Text __instance)
        {
            if (ChineseFont != null && __instance.font != null && __instance.font.GetInstanceID() == ChineseFont.GetInstanceID() && value != null)
            {
                Texture valueTex = value.mainTexture;
                Texture chineseTex = ChineseFont.material.mainTexture;

                if (valueTex != null && chineseTex != null && valueTex.GetInstanceID() != chineseTex.GetInstanceID())
                {
                    int matInstanceId = value.GetInstanceID();
                    if (!MaterialCache.TryGetValue(matInstanceId, out Material cachedMat) || cachedMat == null)
                    {
                        cachedMat = new Material(value);
                        cachedMat.mainTexture = chineseTex;
                        if (ChineseFont.material.HasProperty("_TextureWidth"))
                            cachedMat.SetFloat("_TextureWidth", ChineseFont.material.GetFloat("_TextureWidth"));
                        if (ChineseFont.material.HasProperty("_TextureHeight"))
                            cachedMat.SetFloat("_TextureHeight", ChineseFont.material.GetFloat("_TextureHeight"));
                        if (ChineseFont.material.HasProperty("_GradientScale"))
                            cachedMat.SetFloat("_GradientScale", ChineseFont.material.GetFloat("_GradientScale"));
                        if (ChineseFont.material.HasProperty("_ScaleRatioA"))
                            cachedMat.SetFloat("_ScaleRatioA", ChineseFont.material.GetFloat("_ScaleRatioA"));
                        if (ChineseFont.material.HasProperty("_ScaleRatioB"))
                            cachedMat.SetFloat("_ScaleRatioB", ChineseFont.material.GetFloat("_ScaleRatioB"));
                        if (ChineseFont.material.HasProperty("_ScaleRatioC"))
                            cachedMat.SetFloat("_ScaleRatioC", ChineseFont.material.GetFloat("_ScaleRatioC"));
                        MaterialCache[matInstanceId] = cachedMat;
                        Plugin.Logger.LogInfo("Generated and cached translated material for hover effect with correct sizes.");
                    }
                    value = cachedMat;
                }
            }
        }

        [HarmonyPatch(typeof(TMP_Text), "fontMaterial", MethodType.Setter)]
        [HarmonyPrefix]
        public static void TMP_Text_set_fontMaterial_Prefix(ref Material value, TMP_Text __instance)
        {
            if (ChineseFont != null && __instance.font != null && __instance.font.GetInstanceID() == ChineseFont.GetInstanceID() && value != null)
            {
                Texture valueTex = value.mainTexture;
                Texture chineseTex = ChineseFont.material.mainTexture;

                if (valueTex != null && chineseTex != null && valueTex.GetInstanceID() != chineseTex.GetInstanceID())
                {
                    int matInstanceId = value.GetInstanceID();
                    if (!MaterialCache.TryGetValue(matInstanceId, out Material cachedMat) || cachedMat == null)
                    {
                        cachedMat = new Material(value);
                        cachedMat.mainTexture = chineseTex;
                        if (ChineseFont.material.HasProperty("_TextureWidth"))
                            cachedMat.SetFloat("_TextureWidth", ChineseFont.material.GetFloat("_TextureWidth"));
                        if (ChineseFont.material.HasProperty("_TextureHeight"))
                            cachedMat.SetFloat("_TextureHeight", ChineseFont.material.GetFloat("_TextureHeight"));
                        if (ChineseFont.material.HasProperty("_GradientScale"))
                            cachedMat.SetFloat("_GradientScale", ChineseFont.material.GetFloat("_GradientScale"));
                        if (ChineseFont.material.HasProperty("_ScaleRatioA"))
                            cachedMat.SetFloat("_ScaleRatioA", ChineseFont.material.GetFloat("_ScaleRatioA"));
                        if (ChineseFont.material.HasProperty("_ScaleRatioB"))
                            cachedMat.SetFloat("_ScaleRatioB", ChineseFont.material.GetFloat("_ScaleRatioB"));
                        if (ChineseFont.material.HasProperty("_ScaleRatioC"))
                            cachedMat.SetFloat("_ScaleRatioC", ChineseFont.material.GetFloat("_ScaleRatioC"));
                        MaterialCache[matInstanceId] = cachedMat;
                        Plugin.Logger.LogInfo("fontMaterial: Generated and cached translated material for hover effect with correct sizes.");
                    }
                    value = cachedMat;
                }
            }
        }

        [HarmonyPatch(typeof(TMP_Text), "SetText", new Type[] { typeof(string), typeof(bool) })]
        [HarmonyPrefix]
        public static void TMP_Text_SetText_Prefix(ref string text, TMP_Text __instance)
        {
            TMP_Text_set_text_Prefix(ref text, __instance);
        }
        
        [HarmonyPatch(typeof(TMP_Text), "SetText", new Type[] { typeof(string) })]
        [HarmonyPrefix]
        public static void TMP_Text_SetText1_Prefix(ref string text, TMP_Text __instance)
        {
            TMP_Text_set_text_Prefix(ref text, __instance);
        }

    }
}


