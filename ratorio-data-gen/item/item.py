import config
import difflib
import logging
import os
import re
import requests
import util
from bs4 import BeautifulSoup


item_kind = {
    "短剣": 1,
    "片手剣": 2,
    "両手剣": 3,
    "槍": 4,
    "両手槍": 5,
    "斧": 6,
    "両手斧": 7,
    "鈍器": 8,
    "杖": 9,
    "片手杖": 9,
    "弓": 10,
    "カタール": 11,
    "本": 12,
    "爪": 13,
    "楽器": 14,
    "鞭": 15,
    "手裏剣": 16,
    "風魔手裏剣": 16,
    "ハンドガン": 17,
    "ライフル": 18,
    "ショットガン": 19,
    "ガトリングガン": 20,
    "グレネードガン": 21,
    "兜": 50,
    "鎧": 60,
    "盾": 61,
    "肩にかける物": 62,
    "靴": 63,
    "アクセサリー": 64,
    "アクセサリー(1)": 65,
    "アクセサリー(2)": 66,
}
item_place = {
    "上": 0,
    "中": 1,
    "下": 2,
}
item_equip = {
    "全ての職業": 0,
    "ノービス系を除く全ての職業": 1,
    "ノービス系": 50,
    "ソードマン系": 51,
    "シーフ系 忍者系": 52,
    "アコライト系": 53,
    "アーチャー系": 54,
    "マジシャン系 ソウルリンカー系": 55,
    "マーチャント系": 56,
    "忍者系": 58,
    "ガンスリンガー系": 59,
    # 60 は欠番
    "ナイト系 クルセイダー系": 61,
    "アサシン系 ローグ系": 62,
    "プリースト系 モンク系": 63,
    "ハンター系 バード系 ダンサー系": 64,
    "ウィザード系 セージ系 ソウルリンカー系": 65,
    "ブラックスミス系 アルケミスト系": 66,
    # 67 は欠番
    "影狼系 朧系": 68,
    "リベリオン系": 69,
    "3次職ソードマン系 3次職マーチャント系": 70,
    "ソードマン系 マジシャン系 アコライト系 マーチャント系 ソウルリンカー系": 71,
    "ソードマン系 マーチャント系 シーフ系": 72,
    "マーチャント系 アコライト系": 73,
    "ソードマン系 アコライト系 マーチャント系 シーフ系 バード系 ダンサー系": 74,
    "ソードマン系 マーチャント系 アーチャー系 シーフ系": 75,
    "アーチャー系 ローグ系": 76,
    "マジシャン系 アコライト系 ソウルリンカー系": 77,
    "ソードマン系 アコライト系 マーチャント系 シーフ系": 78,
    "2次職 上位2次職 3次職 4次職 拳聖系 ソウルリンカー系": 79,
    "シーフ ハンター系 ローグ系": 80,
    "プリースト系 アサシン系": 81,
    "上位2次職 3次職 4次職": 82,
    "ソードマン系 アーチャー系 マーチャント系 シーフ系 テコンキッド 拳聖系 ガンスリンガー系": 83,
    "ソードマン系 マーチャント系 シーフ系 テコンキッド 拳聖系": 84,
    "ソードマン系 アコライト系 マーチャント系 シーフ系 テコンキッド 拳聖系": 85,
    "ソードマン系 マーチャント系 テコンキッド 拳聖系": 86,
    "ソードマン系 拳聖系": 87,
    # 88 存在しないので確認できない
    # 89 存在しない（データはあるが、公式で検索ヒットしない）ので確認できない
    "ノービス ソードマン系 マーチャント系 アサシン系": 90,
    # 91 存在しない（データはあるが、公式で検索ヒットしない）ので確認できない
    "スーパーノービス系 3次職ソードマン系 3次職マーチャント系 ギロチンクロス系": 92,
    # 93 存在しないので確認できない
    "ノービス系 マジシャン系 アコライト系 ソウルリンカー系": 94,
    "アークビショップ系 ソーサラー系 星帝系": 95,
    # 96 存在しないので確認できない
    # 97 存在しないので確認できない
    # 98 存在しないので確認できない
    # 99 は欠番
    # 100 存在しないので確認できない
    # 101 存在しないので確認できない
    "シーフ ローグ系": 102,
    # 103 存在しないので確認できない
    # 104 存在しないので確認できない
    # 105 存在しないので確認できない
    # 106 存在しないので確認できない
    # 107 存在しないので確認できない
    "アサシン系": 108,
    # 109 存在しないので確認できない
    "ハンター系": 110,
    # 111 存在しないので確認できない
    # 112 存在しないので確認できない
    "クルセイダー系": 113,
    # 114 存在しないので確認できない
    # 115 存在しないので確認できない
    "ミンストレル系": 116,
    "ダンサー系": 117,
    # 118 存在しないので確認できない
    "アルケミスト系": 119,
    "スーパーノービス系": 120,
    "ロードナイト ルーンナイト系": 121,
    "アサシンクロス ギロチンクロス系": 122,
    "ハイプリースト アークビショップ系": 123,
    "スナイパー レンジャー系": 124,
    "ハイウィザード ウォーロック系": 125,
    "ホワイトスミス メカニック系": 126,
    # 127 存在しないので確認できない(パラディン ロイヤルガード系)
    "チェイサー シャドウチェイサー系": 128,
    "チャンピオン 修羅系": 129,
    "クラウン ミンストレル系": 130,
    "ジプシー ワンダラー系": 131,
    # 132 存在しないので確認できない(プロフェッサー ソーサラー系)
    # 133 存在しないので確認できない(クリエイター ジェネティックー系)
    # 141 存在しないので確認できない"ITEM_EQPFLG_TAEGWON",
    # 142 存在しないので確認できない"ITEM_EQPFLG_SERIES_KENSEI",
    "ソウルリーパー系": 143,
    # 144 は欠番（58を使用）
    # 145 は欠番（59を使用）
    "ルーンナイト系": 146,
    "ギロチンクロス系": 147,
    "アークビショップ系": 148,
    "レンジャー系": 149,
    "ウォーロック系": 150,
    "メカニック系": 151,
    "ロイヤルガード系": 152,
    "シャドウチェイサー系": 153,
    "修羅系": 154,
    "ミンストレル系": 155,
    "ワンダラー系": 156,
    "ソーサラー系": 157,
    "ジェネティック系": 158,
    "ドラゴンナイト": 159,
    "シャドウクロス": 160,
    "カーディナル": 161,
    "ウィンドホーク": 162,
    "アークメイジ": 163,
    "マイスター": 164,
    "インペリアルガード": 165,
    "アビスチェイサー": 166,
    "インクイジター": 167,
    "トルバドゥール": 168,
    "トルヴェール": 169,
    "エレメンタルマスター": 170,
    "バイオロ": 171,
    "天帝": 172,
    "ソウルアセティック": 173,
    "蜃気楼 不知火": 174,
    "ナイトウォッチ": 175,
    "ハイパーノービス": 176,
    "スピリットハンドラー": 177,
    "ミンストレル系 ワンダラー系": 191,
    "4次職 拡張4次職": 192,
    "サモナー系": 201,
}

log = logging.getLogger(__name__)


def get_item_kind(kind, place):
    return item_kind.get(kind, 999) + item_place.get(place[0], 0)


def exist_parameter(lines: list, keyword):
    if f"{keyword} : " in lines:
        return True
    elif f" {keyword} : " in lines:
        return True
    return False


def is_card(lines: list):
    return (
        exist_parameter(lines, "重量")
        and exist_parameter(lines, "系列")
        and get_parameter_value(lines, "系列") == "カード"
    )


def is_equip(lines: list):
    return (
        exist_parameter(lines, "重量")
        and exist_parameter(lines, "系列")
        and get_parameter_value(lines, "系列") != "カード"
    )


def is_item(lines: list):
    return exist_parameter(lines, "重量") and not exist_parameter(lines, "系列")


def is_enchant(lines: list):
    return not exist_parameter(lines, "重量")


def get_parameter_value(lines: list, keyword):
    try:
        return lines[lines.index(f"{keyword} : ") + 1].strip()
    except:
        return lines[lines.index(f" {keyword} : ") + 1].strip()


def get_armor_elemental(blocks: list):
    op = []
    for i in range(1, len(blocks) - 1):
        r = re.match("鎧に(.+)属性を付与する", blocks[i].strip())
        if r:
            elemental = {
                "水": 1,
                "地": 2,
                "火": 3,
                "風": 4,
                "毒": 5,
                "聖": 6,
                "闇": 7,
                "念": 8,
                "死": 9,
            }
            op = [198, int(elemental.get(r.group(1), 99))]
            break
    return op


def create_item(terms):
    r = requests.get(f"https://rotool.gungho.jp/item/{terms[0]}/0/")
    soup = BeautifulSoup(r.text, "html.parser")
    node = soup.select_one("div.description>p.note")
    blocks = node.get_text("<>").split("―――――――――――――")
    lines = blocks[-1].split("<>")
    if is_item(lines):
        log.debug(f"{terms} is item")
        return None
    if is_card(lines):
        # TODO : implement create card.dat
        log.debug(f"{terms} is card")
        return None
    if is_enchant(lines):
        # TODO : implement create card.dat
        log.debug(f"{terms} is enchant")
        return None
    if is_equip(lines):
        log.debug(f"{terms} is equip")
        series = get_parameter_value(lines, "系列")
        place = (
            "-"
            if not exist_parameter(lines, "位置")
            else get_parameter_value(lines, "位置")
        )
        kind = get_item_kind(series, place)
        equip = get_parameter_value(lines, "装備")
        slot = get_parameter_value(lines, "スロット")
        weight = get_parameter_value(lines, "重量")
        rlevel = get_parameter_value(lines, "要求レベル")
        op = []
        if get_parameter_value(lines, "破損") == "しない":
            op.extend([194, 1])
        if kind == 999:
            log.warning(f"未対応[{terms}]")
            return None
        elif kind < 50:  # 武器
            atk = get_parameter_value(lines, "Atk")
            wlevel = get_parameter_value(lines, "武器レベル")
            op.extend(
                [88 if kind == 9 else 100, int(get_parameter_value(lines, "Matk"))]
            )
            if get_parameter_value(lines, "属性") != "無":
                elemental = {
                    "水": 1,
                    "地": 2,
                    "火": 3,
                    "風": 4,
                    "毒": 5,
                    "聖": 6,
                    "闇": 7,
                    "念": 8,
                    "死": 9,
                }
                op.extend(
                    [20, int(elemental.get(get_parameter_value(lines, "属性"), 99))]
                )
        else:  # 防具
            op.extend(get_armor_elemental(blocks))
            atk = get_parameter_value(lines, "Def")
            wlevel = 0
        item_data = [
            9999999999,
            kind,
            item_equip.get(equip, 999),
            int(atk),
            int(wlevel),
            int(slot),
            int(weight),
            int(rlevel),
            terms[1],
            "カナ",
            "0",
        ]
        item_data.extend(op)
        item_data.append(0) # terminator
        return item_data
    return None


def gen_item_dat(items_by_name, cards_by_name):
    from_text = ""
    if os.path.exists(config.id2displayname_path + ".prev"):
        with open(config.id2displayname_path + ".prev", "r") as f:
            from_text = f.readlines()

    if not os.path.exists(config.id2displayname_path):
        log.error(f"File not found.[{config.id2displayname_path}]")
        return
    with open(config.id2displayname_path, "r") as f:
        to_text = f.readlines()

    differ = difflib.Differ()
    diffs = differ.compare(from_text, to_text)
    for diff in diffs:
        if diff[0] != "+":
            continue
        terms = diff.strip()[2:-1].split("#")
        if len(terms) != 2:
            continue
        item_id = util.lookup_item_dict(items_by_name, terms[1])
        card_id = util.lookup_card_dict(cards_by_name, terms[1])
        if item_id != "{item_id}" or card_id != "{card_id}":
            log.debug(f"登録済み [{terms}]")
            continue
        item = create_item(terms)
        print(str(item).replace("'", '"'))

