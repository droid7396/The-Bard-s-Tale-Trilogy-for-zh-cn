#!/usr/bin/env python3
"""
llm_translate.py -- 使用 Gemini API 重新翻譯《冰城傳奇三部曲》繁體中文化文本
特色：
  - 中世紀奇幻 RPG / D&D 術語導向的 System Prompt
  - 批次翻譯（短文本每批30條、劇情長文每批5條）
  - 自動保留 {0} 變數、<color=...> 標籤、\n 換行
  - 斷點續傳：每批完成後立即寫入，重跑時跳過已翻譯項目
  - 支援 --force 強制全部重翻、--only-empty 只翻沒有中文的
"""

import csv
import re
import time
import sys
import os
import argparse

try:
    from openai import OpenAI
except ImportError:
    print("錯誤：請先在終端機執行 `pip install openai` 安裝套件。")
    sys.exit(1)

INPUT_FILE  = "Translation_Tasks.csv"
OUTPUT_FILE = "Translation_Tasks_LLM.csv"
MODEL_NAME  = "deepseek-chat"
DEEPSEEK_API_KEY = "[ENCRYPTION_KEY]"
SHORT_BATCH_SIZE  = 30
LONG_BATCH_SIZE   = 5
SHORT_CHAR_LIMIT  = 240
BATCH_DELAY       = 5.0   # ~12 req/min，保持在 Free Tier 15 RPM 以下
MAX_RETRIES       = 6     # 429/503 最多重試次數

SYSTEM_PROMPT = r"""你是《冰城傳奇三部曲》(The Bard's Tale Trilogy) 繁體中文在地化的專業翻譯員。
這是一款 1985 年的美式中世紀奇幻 RPG，風格接近 D&D 第一版，於 2018 年完全重製。

## 翻譯原則
1. **語境**：中世紀西方奇幻世界，充滿魔法、地下城、怪物、冒險者公會。語氣莊重而略帶古風，偶爾有幽默感。
2. **受眾**：熟悉 D&D / TRPG 的台灣玩家，接受業界通用譯名。
3. **術語一致性**：嚴格按照下方術語表翻譯，不得自創譯名。
4. **專有名詞**：The Bard's Tale / Bard's Tale 必須翻譯為「冰城傳奇」。
5. **不翻譯**：人名（Mangar, Roscoe, Garth, Longinus, Caith, Lestradae 等）和地名（Skara Brae 等）原樣保留。

## 格式規則（絕對不可更改）
- {0} {1} {2} 等變數：原樣保留，不翻譯、不移位
- <color=#ffff22> </color> 等 HTML 標籤：原樣保留
- \n 換行符號：原樣保留在同樣位置（\n 是兩個字元反斜線加n）
- 字串開頭/結尾的空格與標點：盡量保持一致

## 術語表（職業）
Warrior=戰士, Paladin=聖騎士, Rogue=盜賊, Hunter=獵人, Bard=吟遊詩人, Conjurer=咒術師
Magician=幻術師, Sorcerer=術士, Wizard=巫師, Archmage=大法師
Chronomancer=時空術士, Geomancer=大地術士, Monk=武僧, Mage=法師, Magic User=魔法師

## 術語表（屬性）
HP/Hit Points=生命值, SP/Spell Points=法術點數, AC/Armor Class=防禦等級
XP/Experience=經驗值, Str/Strength=力量, Int/Intelligence=智力
Dex/Dexterity=敏捷, Con/Constitution=體質, Lck/Luck=幸運, Level=等級

## 術語表（遊戲系統）
party=冒險隊伍/隊伍, guild=公會, guild master=公會長, Review Board=仲裁委員會
dungeon=地下城, quest=任務, chest=寶箱, trap=陷阱, portal=傳送門, spinner=迷向器
inn=旅館, tavern=酒館, temple=神廟, shoppe/shop=商店, inventory=道具欄/庫存
equip=裝備, melee=近戰, combat=戰鬥, spell=法術, bard song=吟遊詩人之歌
summon=召喚, undead=亡靈, demon=惡魔, petrify/stoned=石化, poisoned=中毒
paralyzed=麻痺, insane/nuts=瘋狂, drained=耗盡, possessed=附身, withered/old=衰老
critical hit=暴擊, level drain=等級吸取, fire=火焰, cold=冰霜, electric=閃電
holy=神聖, water=水系, compass=指南針, levitation=漂浮, light=光源
GROUP=群組, CHAR=角色, CLASS=職業, Damage=傷害, Items=物品

## 術語表（三部曲標題）
Tales of the Unknown=未知傳奇 , The Destiny Knight=天命勇士, Thief of Fate=命運之賊

## 翻譯行為要求
- 直接輸出翻譯結果，不要加解釋、不要加額外說明文字。
- 遊戲 UI 短字串（按鈕文字等）保持簡潔有力。
- 劇情敘述文字要流暢自然，符合中文閱讀習慣。
- 對話引用（"..."）翻成繁中後可用「」或保留""，但要一致。
"""

PH_RE  = re.compile(r'\{\d+\}')
TAG_RE = re.compile(r'<[^>]+>')

def protect_string(s):
    ph_map, tag_map = {}, {}
    ph_c = [0]
    def rep_ph(m):
        i = ph_c[0]; ph_c[0] += 1; ph_map[i] = m.group(0); return f"XPHX{i}XPHX"
    s = PH_RE.sub(rep_ph, s)
    tag_c = [0]
    def rep_tag(m):
        i = tag_c[0]; tag_c[0] += 1; tag_map[i] = m.group(0); return f"XTAGX{i}XTAGX"
    s = TAG_RE.sub(rep_tag, s)
    return s, ph_map, tag_map

def restore_string(s, ph_map, tag_map):
    # Restore tags: replace token with original (preserve surrounding spaces)
    for i, orig in tag_map.items():
        s = s.replace(f'XTAGX{i}XTAGX', orig)
    # Restore placeholders
    for i, orig in ph_map.items():
        s = s.replace(f'XPHX{i}XPHX', orig)
    return s.strip()

# ==========================================
# 強制校正字典 (Post-Processing)
# 在這裡加入您發現的常錯單字，程式會自動替換回來
# ==========================================
DND_GLOSSARY = {
    "吟遊詩人的傳奇": "冰城傳奇",
    "吟遊詩人傳奇": "冰城傳奇",
    "魔法師": "法師", # 避免與 Magic User 混淆
}

def force_glossary(text):
    for wrong, correct in DND_GLOSSARY.items():
        text = text.replace(wrong, correct)
    return text

def translate_batch(client, items):
    lines = []
    for i, (_, key, p_en, _, _) in enumerate(items):
        lines.append(f"===ITEM_{i}===")
        lines.append(p_en)
    lines.append(f"===ITEM_{len(items)}===")
    prompt = "\n".join(lines)

    user_msg = (
        "請將以下遊戲文字段落逐條翻譯成繁體中文。\n"
        "每條以 ===ITEM_N=== 分隔，請在回覆中維持相同分隔格式，\n"
        "在每個 ===ITEM_N=== 之後直接輸出該條的繁體中文翻譯，不要輸出任何說明文字。\n\n"
        + prompt
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.2
            )
            raw = response.choices[0].message.content
            break  # 成功，跳出重試迴圈
        except Exception as e:
            print(f"  ⏳ 連線或推論錯誤（第{attempt}次）：{e}，等待 5 秒後重試...")
            if attempt < MAX_RETRIES:
                time.sleep(5)
            else:
                raise

    results = [""] * len(items)
    pattern = re.compile(r'===ITEM_(\d+)===\s*(.*?)(?====ITEM_\d+===|$)', re.DOTALL)
    for m in pattern.finditer(raw):
        idx = int(m.group(1))
        text = m.group(2).strip()
        if 0 <= idx < len(items):
            results[idx] = text
    final = []
    for i, (_, _, _, ph_map, tag_map) in enumerate(items):
        restored = restore_string(results[i], ph_map, tag_map)
        final.append(force_glossary(restored)) # 套用強制校正字典
    return final

def load_csv(path):
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1:]

def save_csv(path, header, rows):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

def main():
    parser = argparse.ArgumentParser(description="使用 DeepSeek API 翻譯遊戲文本")
    parser.add_argument("--only-empty", action="store_true", help="只翻譯中文欄為空的行")
    parser.add_argument("--force",      action="store_true", help="強制重翻所有行")
    parser.add_argument("--limit",      type=int, default=0,  help="只翻前 N 條（測試用）")
    parser.add_argument("--input",      default=INPUT_FILE)
    parser.add_argument("--output",     default=OUTPUT_FILE)
    args = parser.parse_args()

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    header, rows = load_csv(args.input)

    existing_zh = {}
    if os.path.exists(args.output) and not args.force:
        _, out_rows = load_csv(args.output)
        for r in out_rows:
            if len(r) >= 3 and r[2].strip():
                existing_zh[r[0]] = r[2]
        print(f"斷點續傳：已讀取 {len(existing_zh)} 條已完成翻譯。")

    working_rows = []
    for row in rows:
        r = list(row)
        while len(r) < 3: r.append('')
        if r[0] in existing_zh and not args.force:
            r[2] = existing_zh[r[0]]
        working_rows.append(r)

    to_translate = []
    for i, row in enumerate(working_rows):
        key, en, zh = row[0], row[1], row[2]
        if not en.strip(): continue
        if args.only_empty:
            if not zh.strip(): to_translate.append((i, key, en))
        elif args.force:
            to_translate.append((i, key, en))
        else:
            if key not in existing_zh: to_translate.append((i, key, en))

    if args.limit > 0:
        to_translate = to_translate[:args.limit]

    total = len(to_translate)
    print(f"共需翻譯 {total} 條。")
    if total == 0:
        print("沒有需要翻譯的條目，程式結束。"); return

    def is_long(en, key):
        return key.startswith("SCRIPTSTRING") or len(en) > SHORT_CHAR_LIMIT

    short_items = [(i,k,e) for (i,k,e) in to_translate if not is_long(e,k)]
    long_items  = [(i,k,e) for (i,k,e) in to_translate if  is_long(e,k)]

    def make_batches(items, size):
        return [items[s:s+size] for s in range(0, len(items), size)]

    all_batches = make_batches(short_items, SHORT_BATCH_SIZE) + make_batches(long_items, LONG_BATCH_SIZE)
    print(f"短文本：{len(short_items)} 條 / {len(make_batches(short_items,SHORT_BATCH_SIZE))} 批")
    print(f"長文本：{len(long_items)} 條 / {len(make_batches(long_items,LONG_BATCH_SIZE))} 批")
    print(f"合計：{len(all_batches)} 批\n")

    done = errors = 0
    for batch_num, batch in enumerate(all_batches, 1):
        protected = []
        for (row_idx, key, en) in batch:
            p_en, ph_map, tag_map = protect_string(en)
            protected.append((row_idx, key, p_en, ph_map, tag_map))
        label = f"批次 {batch_num}/{len(all_batches)}"
        try:
            translations = translate_batch(client, protected)
            for (row_idx, key, _, _, _), zh_result in zip(protected, translations):
                if zh_result:
                    working_rows[row_idx][2] = zh_result
                    done += 1
                else:
                    print(f"  警告：翻譯結果為空 [{key}]")
                    errors += 1
            save_csv(args.output, header, working_rows)
            pct = (done + errors) / total * 100
            print(f"[{label}] 完成 {len(batch)} 條 | 累計 {done}/{total} ({pct:.1f}%)")
        except Exception as e:
            print(f"[{label}] 錯誤：{e}")
            errors += 1
            save_csv(args.output, header, working_rows)
        if batch_num < len(all_batches):
            time.sleep(BATCH_DELAY)

    print(f"\n翻譯完成！成功 {done} 條，錯誤 {errors} 條。")
    print(f"結果儲存至：{args.output}")

if __name__ == "__main__":
    main()
