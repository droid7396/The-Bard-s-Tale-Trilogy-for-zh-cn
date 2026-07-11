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
    [BepInPlugin("com.antigravity.zhlocalizer", "ZH Localizer", "2.0.0")]
    public class Plugin : BasePlugin
    {
        public static BepInEx.Logging.ManualLogSource Logger;
        public static string CachedLocalizationXml = null;
        public static List<Tuple<Regex, string>> CombatRegexes = new List<Tuple<Regex, string>>();

        public override void Load()
        {
            Logger = Log;
            Logger.LogInfo("ZHLocalizer 2.0.0 Plugin Loaded!");
            
            // Pre-load our translated XML
            string xmlPath = Path.Combine(Paths.PluginPath, "btr_localization_zh.txt");
            try
            {
                if (File.Exists(xmlPath))
                {
                    CachedLocalizationXml = File.ReadAllText(xmlPath);
                    Logger.LogInfo("Loaded translated btr_localization_zh.txt successfully!");
                }
                else
                {
                    Logger.LogError("Could not find btr_localization_zh.txt in BepInEx/plugins/");
                }
            }
            catch (Exception ex)
            {
                Logger.LogError("Failed to load btr_localization_zh.txt: " + ex);
            }

            // Load Combat Regexes
            string combatDict = Path.Combine(Paths.PluginPath, "combat_translations.txt");
            try
            {
                if (File.Exists(combatDict))
                {
                    foreach (var line in File.ReadAllLines(combatDict))
                    {
                        if (string.IsNullOrWhiteSpace(line) || line.StartsWith("#")) continue;
                        var parts = line.Split(new string[] { "::ZH::" }, StringSplitOptions.None);
                        if (parts.Length == 2)
                        {
                            CombatRegexes.Add(new Tuple<Regex, string>(new Regex(parts[0], RegexOptions.IgnoreCase), parts[1].Replace("\\n", "\n")));
                        }
                    }
                    Logger.LogInfo($"Loaded {CombatRegexes.Count} combat regex rules!");
                }
            }
            catch (Exception ex)
            {
                Logger.LogError("Failed to load combat_translations.txt: " + ex);
            }

            // Apply Harmony patches
            Harmony.CreateAndPatchAll(typeof(Hooks));
            
            // Add font injection behaviour
            AddComponent<FontInjectorBehaviour>();
        }
    }

    // ==========================================================
    // 周期性字型掃描器 - 確保所有新生成的 TMP_Text 都會套用中文字型
    // ==========================================================
    public class FontInjectorBehaviour : MonoBehaviour
    {
        private float _timer = 0f;
        private const float SCAN_INTERVAL = 0.2f;
        private UnityEngine.SceneManagement.Scene _dontDestroyOnLoadScene;
        private bool _hasDontDestroyScene = false;

        void Start()
        {
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
            } 
            catch { }
        }

        private void ScanGO(GameObject go)
        {
            if (go == null || !go.activeInHierarchy) return;
            
            var tmp = go.GetComponent<TMP_Text>();
            if (tmp != null && tmp.font != Hooks.ChineseFont)
            {
                // 只替換含有中文字元的文本，或是強制全部替換
                if (string.IsNullOrEmpty(tmp.text) || Regex.IsMatch(tmp.text, @"\p{IsCJKUnifiedIdeographs}"))
                {
                    tmp.font = Hooks.ChineseFont;
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

        // ==========================================================
        // 攔截 TextAsset (原生地代替換)
        // ==========================================================
        [HarmonyPatch(typeof(UnityEngine.TextAsset), "text", MethodType.Getter)]
        [HarmonyPostfix]
        public static void TextAsset_get_text_Postfix(UnityEngine.TextAsset __instance, ref string __result)
        {
            if (__instance != null && !string.IsNullOrEmpty(__instance.name))
            {
                if (__instance.name.Contains("btr_localization"))
                {
                    if (!string.IsNullOrEmpty(Plugin.CachedLocalizationXml))
                    {
                        __result = Plugin.CachedLocalizationXml;
                        Plugin.Logger.LogInfo("Successfully intercepted and replaced btr_localization via TextAsset.text!");
                    }
                }
            }
        }



        // ==========================================================
        // TMP_Text 字型處理
        // ==========================================================
        [HarmonyPatch(typeof(TMP_Text), nameof(TMP_Text.text), MethodType.Setter)]
        [HarmonyPrefix]
        public static void TMP_Text_set_text_Prefix(ref string value, TMP_Text __instance)
        {
            if (string.IsNullOrEmpty(value)) return;

            // Apply combat regex translations
            if (Plugin.CombatRegexes.Count > 0)
            {
                foreach (var rule in Plugin.CombatRegexes)
                {
                    if (rule.Item1.IsMatch(value))
                    {
                        value = rule.Item1.Replace(value, rule.Item2);
                        break;
                    }
                }
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

            // Always inject Chinese font if Chinese characters are present
            bool hasChineseChars = Regex.IsMatch(value, @"\p{IsCJKUnifiedIdeographs}");
            
            if (hasChineseChars)
            {
                if (ChineseFont != null)
                {
                    __instance.font = ChineseFont;
                }
                
                // Keep the line-height fix just in case the UI is still a bit tight
                if (!value.StartsWith("<line-height="))
                {
                    value = "<line-height=130%>" + value;
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
                    }
                    value = cachedMat;
                }
            }
        }

        [HarmonyPatch(typeof(TMP_Text), "fontMaterial", MethodType.Setter)]
        [HarmonyPrefix]
        public static void TMP_Text_set_fontMaterial_Prefix(ref Material value, TMP_Text __instance)
        {
            TMP_Text_set_fontSharedMaterial_Prefix(ref value, __instance);
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
