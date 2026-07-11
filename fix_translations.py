"""
批次修正 Translation_Tasks.csv 中的機翻錯誤
- 修正特定 KEY 對應的錯誤翻譯（縮寫、職業名、屬性名）
- 對中文欄位進行全文搜尋取代，修正高頻錯誤術語
"""
import csv
import re

input_file = 'Translation_Tasks.csv'
output_file = 'Translation_Tasks.csv'

# ============================================================
# 1. 針對特定 KEY，直接覆蓋整個中文欄位的值
# ============================================================
KEY_FIXES = {
    # === 職業縮寫（遊戲 UI 狀態欄，對應角色職業）===
    'WA': '戰士',
    'PA': '聖騎士',
    'MO': '武僧',
    'RO': '盜賊',
    'HU': '獵人',
    'BA': '吟遊詩人',
    'CO': '咒術師',
    'MA': '幻術師',
    'SO': '巫師',
    'WI': '術士',
    'AM': '大法師',
    'CH': '時空術士',
    'GE': '大地術士',
    'HP': 'HP',
    'SP': 'SP',
    'CL': 'CL',
    'AC': 'AC',

    # === 屬性縮寫 ===
    'Str': '力',
    'Int': '智',
    'Dex': '敏',
    'Con': '體',
    'Lck': '運',
    'Lv': 'Lv',
    'XP': 'XP',

    # === 屬性全名 ===
    'Strength': '力量',
    'Intelligence': '智力',
    'Dexterity': '敏捷',
    'Constitution': '體質',
    'Luck': '幸運',

    # === 職業名稱（全名）===
    'Warrior': '戰士',
    'Paladin': '聖騎士',
    'Rogue': '盜賊',
    'Bard': '吟遊詩人',
    'Hunter': '獵人',
    'Monk': '武僧',
    'Conjurer': '咒術師',
    'Magician': '幻術師',
    'Sorcerer': '巫師',
    'Wizard': '術士',
    'Archmage': '大法師',
    'Chronomancer': '時空術士',
    'Geomancer': '大地術士',
    'Monster': '怪物',
    'Illusion': '幻象',

    # === 狀態標籤（大寫縮寫）===
    'STUN': '暈眩',
    'NUTS': '瘋狂',
    'POSS': '附身',
    'HIDE': '潛伏',
    'ANIMATE': '動死',
    'PARA': '麻痺',
    'POIS': '中毒',
    'OLD': '衰老',
    'DRAIN': '吸取',
    'STONED': '石化',
    'DEAD': '死亡',
    'Level': '等級',

    # === 傷害類型 ===
    'Melee': '近戰',
    'Breath': '噴吐',
    'Range': '遠程',
    'Chance': '隨機',
    'Defend': '防禦',
    'Spell': '法術',
    'Damage': '傷害',
    'Electric': '閃電',
    'Cold': '冰凍',
    'Holy': '神聖',
    'Water': '水系',
    'Fire': '火焰',
    'Item': '物品',
    'Items': '物品',
    'Light': '光源',
    'Sight': '視野',
    'Levitation': '漂浮',
    'Compass': '指南針',
    'Song': '歌謠',
    'Duration': '持續時間',
    'Persistent': '永久',
    'Stone': '石化',

    # === 狀態條件 ===
    'Injured': '受傷',
    'Normal': '正常',
    'Cond_Poisoned': '中毒',
    'Cond_Old': '衰老',
    'Cond_Dead': '死亡',
    'Cond_Stoned': '石化',
    'Cond_Paralyzed': '麻痺',
    'Cond_Possessed': '附身',
    'Cond_Insane': '瘋狂',
    'Cond_Drained': '精力耗盡',

    # === 種族名稱 ===
    'Human': '人類',
    'Elf': '精靈',
    'Dwarf': '矮人',
    'Hobbit': '哈比人',
    'HalfElf': '半精靈',
    'HalfOrc': '半獸人',
    'Gnome': '侏儒',
    'Male': '男性',
    'Female': '女性',
    'Undead': '亡靈',
    'Demon': '惡魔',

    # === UI 術語 ===
    'Classes': '職業',
    'Slot': '欄位',
    'Unidentified': '未鑑定',
    'Equipped': '已裝備',
    'Reroll': '重新投骰',
    'Accept Character': '確認角色',
    'Disarm Skill': '解除陷阱技能',
    'Identify Skill': '鑑定技能',
    'Hide in Shadows Skill': '潛伏陰影技能',
    'Disarm Traps': '拆除陷阱',
    'Hide in Shadows': '潛伏陰影',
    'Pool Gold': '集中金幣',
    'Container': '容器',
    'Instrument': '樂器',
    'Figurine': '小雕像',
    'Helm': '頭盔',
    'Helm_DIVIDER': '頭盔',
    'Instrument_DIVIDER': '樂器',
    'Figurine_DIVIDER': '小雕像',
    'Party': '隊伍',
    'PARTY_INVENTORY': '隊伍背包',

    # === 裝備特效 ===
    'Breath Protection': '噴吐防護',
    'Bonus to Run': '逃跑加成',
    'Regen Hitpoints': '生命再生',
    'Regen Spellpoints': '法術再生',
    'Double Spell Regen': '雙倍法術再生',
    'Quarter Spell Cost': '四分之一法術消耗',
    'Calm Monster': '鎮定怪物',
    'Hide Bonus': '潛伏加成',
    'Luck Bonus': '幸運加成',
    'Bonus to Hit': '命中加成',
    'To Hit': '命中',
    'Summon Help': '召喚援軍',

    # === 特定欄位 ===
    'Summon': '召喚',
    'Spirits': '靈魂',
    'Illusion': '幻象',
    'Attack': '攻擊',
    'Unarmed Combat': '徒手格鬥',
    'Damage Min': '最低傷害',
    'Damage Max': '最高傷害',
    'Ranged Damage Min': '最低遠程傷害',
    'Ranged Damage Max': '最高遠程傷害',
    'Unidentified Special': '未知特效',
    'Review Board': '評審委員會',
    'The Review Board': '評審委員會',
    'SPECIAL_SLOT': '特殊',
    'Spells': '法術',
    'Magic User': '魔法師',
    'Combat Round': '戰鬥回合',
    'Bard Song': '吟遊詩人之歌',
    'Stop Singing': '停止演奏',
    'STOP_SINGING_HINT': '停止演奏當前歌謠',
    'CHOOSE_SONG': '選擇要演奏的歌謠',
    'LEVEL_1': 'Lv1',
    'LEVEL_2': 'Lv2',
    'LEVEL_3': 'Lv3',
    'LEVEL_4': 'Lv4',
    'LEVEL_5': 'Lv5',
    'End of Combat': '戰鬥結束',
    'Silence': '沉默',
    'Mage': '法師',
    'Ranged attack': '遠程攻擊',
    'Run away': '逃跑',
    'Fight bravely': '奮勇戰鬥',
    'Advance ahead': '向前推進',
    'Done': '完成',
    'Inventory': '背包',
    'Trade Gold': '轉移金幣',
    'INVENTORY_EMPTY': '背包已空。',
    'TRADE_ITEM': '將物品轉給其他隊員',
    'Drop item': '丟棄物品',
    'EQUIP_UNEQUIP': '裝備/卸下',
    'Use item': '使用物品',
    'Stack items': '堆疊物品',
    'Identify': '鑑定',
    'Back': '返回',
    'Resurrection': '復活',
}

# ============================================================
# 2. 全文搜尋取代（針對「中文欄位」中的錯誤術語）
#    格式：(舊詞, 新詞)
#    注意順序：長詞優先，避免部分取代
# ============================================================
GLOBAL_FIXES = [
    # 高頻遊戲術語
    ('派對庫存', '隊伍背包'),
    ('派對（無指南針）', '隊伍（無指南針）'),
    ('派對', '隊伍'),     # 要在「派對庫存」後面才替換
    ('專案', '物品'),
    ('損壞', '傷害'),
    ('承受我的智慧', '負擔我的報酬'),
    ('審查委員會', '評審委員會'),
    # 職業名稱一致化
    ('法師之火', '魔法火焰'),
    ('嚮導', '術士'),
    # 縮寫一致化（已在KEY_FIXES修正，這裡補強）
    ('課程', '職業'),    # Classes -> 課程 -> 職業
    # 物品相關
    ('加斯', 'Garth'),
    ('羅斯科', 'Roscoe'),
    ('貨櫃', '容器'),
    ('儀器儀表', '樂器'),
    ('小雕像', '小雕像'),
    # 狀態相關
    ('身份不明', '未鑑定'),
    ('裝備齊全', '已裝備'),
    # UI 相關
    ('英式撞球金', '集中金幣'),
    ('重新滾動', '重新投骰'),
    ('接受字符', '確認角色'),
    ('按項目降低成本', '物品降低費用'),
    ('隱藏在陰影中的技能', '潛伏陰影技能'),
    ('隱藏在陰影中', '潛伏於陰影'),
    ('躲在陰影裡', '潛伏於陰影'),
    ('跳開了', '閃避了'),
    ('分配奧術', '奧術傳送'),
    ('阿普奧術', '奧術傳送'),
    ('一個身份不明的', '一個未鑑定的'),
    ('身份不明的', '未鑑定的'),
    # 戰鬥相關
    ('保衛', '防禦'),
    ('呼吸防護', '噴吐防護'),
    ('呼吸', '噴吐'),      # Breath 在戰鬥中
    ('吟遊詩人之歌', '吟遊詩人之歌'),  # 保留不動
    ('宋', '歌謠'),         # Song -> 宋 -> 歌謠
    ('持久的', '永久'),
    ('水平排水', '等級吸取'),
    ('汲極', '吸取'),
    ('興趣點資訊系統', '中毒'),
    ('銷售點服務系統', '附身'),
    ('史東德', '石化'),
    ('瀝乾', '精力耗盡'),
    ('帕拉', '麻痺'),
    ('勒克', '幸運'),
    ('斯特', '力量'),
    ('靈巧性', '敏捷'),
    ('實力', '力量'),
    ('情報', '智力'),
    ('憲法', '體質'),
    ('運行獎金', '逃跑加成'),
    ('隱藏獎金', '潛伏加成'),
    ('幸運獎金', '幸運加成'),
    ('再生法術點', '法術再生'),
    ('雙法術回复', '雙倍法術再生'),
    ('季度法術費用', '四分之一法術消耗'),
    ('一半法術費用', '一半法術消耗'),
    ('恢復生命值', '生命再生'),
    ('冷靜的怪物', '鎮定怪物'),
    ('無旋轉', '防旋轉'),
    # 職業名稱
    ('時空漫遊者', '時空術士'),
    ('風水師', '大地術士'),
    ('和尚', '武僧'),
    # 地名專有名詞修正（Garth、Roscoe）
    ('加斯就不會保留它', 'Garth 就不會保留它'),
    ('把它帶到加斯那裡去辨認它', '把它帶去 Garth 的店鑑定'),
    # 其他細節
    ('你們的政黨不相信', '你的隊伍不信'),
    ('黨員', '隊員'),
    ('黨前進', '隊伍前進'),
    ('黨受到保護', '隊伍受到保護'),
    ('黨被治愈', '隊伍被治癒'),
    ('另一位黨員', '另一位隊員'),
    ('大量拼字', '批次法術'),
    ('的妝容', '的角色'),
    ('當你能承受我的智慧時就回來吧', '等你有足夠的金幣再來'),
    # 地下城術語
    ('地牢', '地下城'),
    ('解除武裝技能', '解除陷阱技能'),
    ('解除武裝', '解除'),
    ('烈酒', '靈魂'),
    ('插槽', '欄位'),
    # 書名統一
    ('《吟遊詩人的故事》', '《冰城傳奇》'),
]

def fix_csv():
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
    
    header = reader[0]
    rows = reader[1:]
    
    key_fixed = 0
    global_fixed = 0
    
    # 建立 KEY -> 行索引的映射（只取第一欄作為 key）
    for i, row in enumerate(rows):
        if len(row) < 3:
            continue
        
        key = row[0].strip()
        zh = row[2].strip()
        
        # --- 1. 針對特定 KEY 直接覆蓋 ---
        if key in KEY_FIXES:
            new_zh = KEY_FIXES[key]
            if row[2] != new_zh:
                print(f"  [KEY修正] {key}: '{row[2]}' -> '{new_zh}'")
                row[2] = new_zh
                key_fixed += 1
    
    print(f"\n[KEY修正完成] 共修正 {key_fixed} 條")
    print("\n[開始全文修正]...")
    
    # --- 2. 全文搜尋取代 ---
    for old_term, new_term in GLOBAL_FIXES:
        for i, row in enumerate(rows):
            if len(row) < 3:
                continue
            
            old_zh = row[2]
            if old_term in old_zh:
                new_zh = old_zh.replace(old_term, new_term)
                if new_zh != old_zh:
                    row[2] = new_zh
                    global_fixed += 1
    
    print(f"[全文修正完成] 共修正 {global_fixed} 處")
    
    # 寫回檔案
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    
    print(f"\n✅ 修正完成！已儲存至 {output_file}")
    print(f"   KEY 精準修正：{key_fixed} 條")
    print(f"   全文取代修正：{global_fixed} 處")

if __name__ == '__main__':
    fix_csv()
