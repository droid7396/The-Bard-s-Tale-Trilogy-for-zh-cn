# The Bard's Tale Trilogy 简体中文汉化（基于 pmanyeh 繁体 Mod）

本项目基于 [pmanyeh/The-Bard-s-Tale-Trilogy-for-zh](https://github.com/pmanyeh/The-Bard-s-Tale-Trilogy-for-zh)（繁體中文化 MOD V1.0.1），通过 OpenCC（`tw2sp`：台湾正体 → 大陆简体 + 词汇转换）将翻译字典转换为简体中文。框架、插件与字体均来自上游，本仓库只包含**转换脚本与简体字典产物**。

## 安装步骤（两步）

1. **安装繁体 Mod 框架**：到 [上游 Releases](https://github.com/pmanyeh/The-Bard-s-Tale-Trilogy-for-zh/releases) 下载 `TheBardsTaleTrilogy_ZH_Mod_for_x64_v1.0.1.zip`，解压全部内容到游戏根目录（`TheBardsTaleTrilogy.exe` 所在位置）。
2. **替换为简体字典**：下载本仓库 `simplified_out/` 下的 `btr_localization_zh.txt` 与 `combat_translations.txt`，覆盖到游戏目录的 `BepInEx\plugins\` 下。

启动游戏即可。首次启动会黑屏 1–3 分钟（IL2CPP 正在生成 interop 缓存），请耐心等待，之后启动恢复正常。

> 谜语门照旧使用游戏内键盘输入**英文答案**，可参考 `simplified_out/riddle_answers.csv` 对照表。

## 自行转换 / 更新

繁体字典更新后，重新生成简体版只需：

```bash
pip install opencc-python-reimplemented
python convert_to_simplified.py
```

脚本会读取已安装的 `BepInEx/plugins/` 中的繁体字典，转换后输出到 `simplified_out/`。只转换含汉字的内容，文件结构、正则、富文本标签均保持不变。

## 技术说明

- 主字典为游戏原生 localization 格式（`KEY:` / `EN:` 字段），插件通过 BepInEx hook `TextAsset.text` 在运行时整体替换
- 字体 AssetBundle 覆盖整个 CJK 基本区（20902 字），简体字典全部用字均已验证在图集内，无缺字
- 启动日志中的 `ERROR IN KEY` 来自上游字典将 `@@...@@` 多行块压平为单行的格式问题（繁体版同样存在），不影响主流程文本显示
