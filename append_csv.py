import csv

lines = open('Translation_Tasks_LLM.csv', 'r', encoding='utf-8-sig').readlines()
lines = [l for l in lines if not l.startswith('SPELL_TOOLTIP_1') and not l.startswith('SPELL_TOOLTIP_2')]
open('Translation_Tasks_LLM.csv', 'w', encoding='utf-8-sig').writelines(lines)

with open('Translation_Tasks_LLM.csv', 'a', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['SPELL_TOOLTIP_1', "{0} ({1}') {2} Lv {3} {4}", "{0} ({1}') {2} Lv {3}\\n{4}"])
    writer.writerow(['SPELL_TOOLTIP_2', '{0} {1} Lv {2} {3}', '{0} {1} Lv {2}\\n{3}'])
    writer.writerow(['PARTY_INV_SPRITE', '<sprite name="LeftDivider">Party Inventory<sprite name="RightDivider">', '<sprite name="LeftDivider">隊伍庫存<sprite name="RightDivider">'])
    writer.writerow(['INV_SPACE', '<color=#ffff00>SPACE</color> Equip/Unequip', '<color=#ffff00>SPACE</color> 裝備/卸下'])
    writer.writerow(['INV_DROP', '<color=#ffff22>D</color>rop item', '<color=#ffff22>D</color> 丟棄物品'])
    writer.writerow(['INV_USE', '<color=#ffff22>U</color>se item', '<color=#ffff22>U</color> 使用物品'])
    writer.writerow(['SLOT_ARMOR', 'Slot: Armor', '欄位：防具'])
    writer.writerow(['SLOT_WEAPON', 'Slot: Weapon', '欄位：武器'])
    writer.writerow(['SLOT_X', 'Slot: {0}', '欄位：{0}'])
    writer.writerow(['EQUIPPED_X', 'Equipped: {0}', '已裝備：{0}'])
    writer.writerow(['DAMAGE_MIN_X', 'Damage Min: {0}', '最小傷害：{0}'])
    writer.writerow(['DAMAGE_MAX_X', 'Damage Max: {0}', '最大傷害：{0}'])
    writer.writerow(['CLASSES_ALL', 'Classes: All Classes', '適用職業：所有職業'])
