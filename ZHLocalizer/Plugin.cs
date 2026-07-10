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
            if (File.Exists(dictPath))
            {
                foreach (string line in File.ReadAllLines(dictPath))
                {
                    if (string.IsNullOrWhiteSpace(line) || line.StartsWith("#")) continue;
                    var parts = line.Split(new[] { '=' }, 2);
                    if (parts.Length == 2)
                    {
                        string key = parts[0].Trim().Replace("\\n", "\n");
                        string val = parts[1].Trim().Replace("\\n", "\n");
                        
                        if (Regex.IsMatch(key, @"\{\d+\}"))
                        {
                            try
                            {
                                string pattern = Regex.Escape(NormalizeText(key));
                                pattern = Regex.Replace(pattern, @"\\\{(\d+)\\\}", "(?<$1>.*?)");
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
                            string normalizedKey = NormalizeText(key);
                            Translations[normalizedKey] = val;
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

            // Apply Harmony patches
            Harmony.CreateAndPatchAll(typeof(Hooks));
        }
    }

    public class Hooks
    {
        public static TMP_FontAsset ChineseFont = null;
        public static bool FontLoaded = false;

        [HarmonyPatch(typeof(TMP_Text), nameof(TMP_Text.text), MethodType.Setter)]
        [HarmonyPrefix]
        public static void TMP_Text_set_text_Prefix(ref string value, TMP_Text __instance)
        {
            if (string.IsNullOrEmpty(value)) return;
            
            bool isTranslated = false;
            string translatedResult = value;
            
            string normalizedValue = Plugin.NormalizeText(value);

            if (Plugin.Translations.TryGetValue(normalizedValue, out string translated))
            {
                translatedResult = translated;
                isTranslated = true;
            }
            else if (Plugin.TranslationCache.TryGetValue(normalizedValue, out translated))
            {
                translatedResult = translated;
                isTranslated = true;
            }
            else
            {
                foreach (var kvp in Plugin.RegexTranslations)
                {
                    Match m = kvp.Key.Match(normalizedValue);
                    if (m.Success)
                    {
                        translatedResult = kvp.Value;
                        foreach (Group group in m.Groups)
                        {
                            if (int.TryParse(group.Name, out _))
                            {
                                translatedResult = translatedResult.Replace("{" + group.Name + "}", group.Value);
                            }
                        }
                        Plugin.TranslationCache[normalizedValue] = translatedResult;
                        isTranslated = true;
                        break;
                    }
                }
            }

            if (isTranslated)
            {
                value = translatedResult;

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
        }
    }
}
