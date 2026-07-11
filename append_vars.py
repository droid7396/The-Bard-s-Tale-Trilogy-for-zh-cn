import csv
import os

new_rows = [
    ["UI_Yes", "<color=#ffff22>Y</color>es", "<color=#ffff22>是</color>"],
    ["UI_No", "<color=#ffff22>N</color>o", "<color=#ffff22>否</color>"],
    ["UI_ExitBuilding", "<color=#ffff22>E</color>xit building", "<color=#ffff22>離</color>開建築"],
    ["UI_FightBravely", "<color=#ffff22>F</color>ight bravely", "<color=#ffff22>英</color>勇戰鬥"],
    ["UI_RunAway", "<color=#ffff22>R</color>un away", "<color=#ffff22>逃</color>跑"],
    ["UI_AttackFoes", "<color=#ffff22>A</color>ttack foes", "<color=#ffff22>攻</color>擊敵人"],
    ["UI_Defend", "<color=#ffff22>D</color>efend", "<color=#ffff22>防</color>禦"],
    ["UI_PartyAttack", "<color=#ffff22>P</color>arty attack", "<color=#ffff22>隊</color>伍攻擊"],
    ["UI_EquipItem", "<color=#ffff22>E</color>quip or Unequip a single item", "<color=#ffff22>裝</color>備或卸下單一物品"],
    ["UI_BardSong", "<color=#ffff22>B</color>ard song", "<color=#ffff22>吟</color>遊詩人歌曲"],
    ["UI_UseItem", "<color=#ffff22>U</color>se an equipped item", "<color=#ffff22>使</color>用已裝備物品"],
    ["UI_RangedAttack", "<color=#ffff22>R</color>anged attack (30')", "<color=#ffff22>遠</color>程攻擊 (30')"],
    ["UI_CastSpell", "<color=#ffff22>C</color>ast a spell", "<color=#ffff22>施</color>放法術"],
    ["UI_HideShadows", "<color=#ffff22>H</color>ide in the shadows ({0}% Chance)", "<color=#ffff22>躲</color>藏在陰影中 ({0}% 機率)"],
    ["UI_All", "All", "全部"],
    ["VAR_Level_Gender_Race_Class", "Level {0} {1} {2} {3}", "第{0}級 {1}{2}{3}"],
    ["VAR_Gender_Race_Class", "{0} {1} {2}", "{0}{1}{2}"],
    ["VAR_Name_Class", "{0} ({1})", "{0}（{1}）"],
    ["VAR_Spell_Range", "{0} ({1}')", "{0} ({1}')"],
    ["VAR_Spell_Code_Range", "{0} ({1}') ({2} Target)", "{0} ({1}') ({2}目標)"],
    ["VAR_Level_Exp", "Level: {0} Experience: {1}/{2}", "等級：{0} 經驗值：{1}/{2}"],
    ["VAR_StrIntDex", "Strength: {0} Intelligence: {1} Dexterity: {2}", "力量：{0} 智力：{1} 敏捷：{2}"],
    ["VAR_ConLuck", "Constitution: {0} Luck: {1}", "體質：{0} 運氣：{1}"],
    ["VAR_HpSp", "Hit Points: {0}/{1} Spell Points: {2}/{3}", "生命值：{0}/{1} 法力值：{2}/{3}"],
    ["VAR_ConjMag", "Conjurer: {0} Magician: {1}", "魔術師：{0} 魔法師：{1}"],
    ["VAR_SorcWiz", "Sorcerer: {0} Wizard: {1}", "巫師：{0} 巫師：{1}"],
    ["VAR_Class_Lv", "{0} Lv {1}", "{0} Lv {1}"],
    ["UI_Single", "Single", "單體"],
    ["UI_Group", "Group", "群體"],
    ["UI_Any", "Any", "任何"],
    ["UI_None", "None", "無"]
]

csv_path = "Translation_Tasks_LLM.csv"

# Read existing keys to avoid duplicates
existing_keys = set()
if os.path.exists(csv_path):
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                existing_keys.add(row[0])

# Append new rows
with open(csv_path, 'a', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    added = 0
    for row in new_rows:
        if row[0] not in existing_keys:
            writer.writerow(row)
            added += 1

print(f"Added {added} rows to {csv_path}")
