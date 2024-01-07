import logging
import math
import mojimoji
import re
import pykakasi

log = logging.getLogger(__name__)


def strip_slot(name: str):
    r = re.match("(.*)\[\d\]", name.strip())
    if r:
        return r.group(1)
    return name


def lookup_item_dict(items: list, name: str):
    name = strip_slot(name)
    item_id = items.get(name, None)
    if item_id is None:
        log.warning(f"item not found [{name}]")
        item_id = "{item_id}"
    return item_id


def lookup_card_dict(cards: dict, name: str):
    if type(name) == int:
        return name
    name = (
        name.replace("（", "(")
        .replace("）", ")")
        .replace("＜", "")
        .replace("＞", "")
        .replace("<", "")
        .replace(">", "")
        .replace(" - ", "-")
        .replace(" + ", "+")
        .replace("Matk1", "Matk+1%")
        .replace("Matk2", "Matk+2%")
        .replace("Matk3", "Matk+3%")
        .replace("Atk+4%", "Atk4")
    )
    card_id = cards.get(name, None)
    if card_id is None:
        log.warning(f"card not found [{name}]")
        card_id = "{card_id}"
    return card_id


def convert_kana_code(kana):
    def sub(baseCode, base, another=False):
        letterIndex = 0
        # ア～オ
        if (0x30A1 <= baseCode) and (baseCode <= 0x30AA):
            letterIndex = math.floor((baseCode - 0x30A1) / 2)
        # カ～チ
        elif baseCode <= 0x30C2:
            letterIndex = 5 + math.floor((baseCode - 0x30AB) / 2)
        # ツ
        elif baseCode <= 0x30C5:
            letterIndex = 17
        # テ～ト
        elif baseCode <= 0x30C9:
            letterIndex = 18 + math.floor((baseCode - 0x30C6) / 2)
        # ナ～ノ
        elif baseCode <= 0x30CE:
            letterIndex = 20 + (baseCode - 0x30CA)
        # ハ～ホ
        elif baseCode <= 0x30DD:
            letterIndex = 25 + math.floor((baseCode - 0x30CF) / 3)
        # マ～モ
        elif baseCode <= 0x30E2:
            letterIndex = 30 + (baseCode - 0x30DE)
        # ヤ～ヨ
        elif baseCode <= 0x30E8:
            letterIndex = 35 + math.floor((baseCode - 0x30E3) / 2)
        # ラ～ロ
        elif baseCode <= 0x30ED:
            letterIndex = 40 + (baseCode - 0x30E9)
        # ワ
        elif baseCode <= 0x30EF:
            letterIndex = 45
        # ヲ～ン
        elif baseCode <= 0x30F3:
            letterIndex = 46 + (baseCode - 0x30F0)
        # ヴ
        elif baseCode <= 0x30F4:
            letterIndex = 52
        # 数字
        elif (0xFF10 <= baseCode) and (baseCode <= 0xFF19):
            return "0" + chr(ord("0") + (baseCode - 0xFF10))
        # 英大文字
        elif (0xFF21 <= baseCode) and (baseCode <= 0xFF3A):
            return "0" + chr(ord("A") + (baseCode - 0xFF21))
        # 上記以外（許容しない文字）
        else:
            return "XX"
        # 行番号、列番号取得
        rowIndex = math.floor(letterIndex / 5)
        columnIndex = str((letterIndex % 5) + 1)
        
        if base:
            return (base + columnIndex)

        rrtRowLetter = chr(ord("A") + rowIndex)
        if another:
            rrtRowLetter = rrtRowLetter.lower()
        return (rrtRowLetter + columnIndex)


    kanaCode = ""
    kks = pykakasi.kakasi()
    for c in mojimoji.han_to_zen(kana):
        charText = c
        charCode = ord(c)
		# 平仮名は片仮名に変換
        if (0x3041 <= charCode) and (charCode <= 0x309F):
            charCode += 0x0060
            charText = chr(charCode)
        # 英小文字は英大文字に変換
        elif (0xFF41 <= charCode) and (charCode <= 0xFF5F):
            charCode -= 0x0020
            charText = chr(charCode)

        # 促音仮名の場合
        if charText in "ッ":
            # 文字コードを１つ後ろへずらして追加する（大文字にする）
            kanaCode += sub(charCode + 1, "z")
        # ウ濁音仮名の場合
        elif charText in "ヴ":
            # 文字コードを「ウ」にして追加する（清音にする）
            kanaCode += sub(ord("ウ"), "v")
        # 小文字仮名の場合
        elif charText in "ァィゥェォャュョヮ":
            # 文字コードを１つ後ろへずらして追加する（大文字にする）
            kanaCode += sub(charCode + 1, None, True)
        # 濁音仮名の場合
        elif charText in "ガギグゲゴザジズゼゾダヂヅデドバビブベボ":
            # 文字コードを１つ前へずらして追加する（清音にする）
            kanaCode += sub(charCode - 1, None, True)
        # 半濁音仮名の場合
        elif charText in "パピプペポ":
            # 文字コードを２つ前へずらして追加する（清音にする）
            kanaCode += sub(charCode - 2, "y", False)
        # 伸ばし棒の場合は、直前の文字の母音を採用する
        elif charText in "ー":
            if len(kanaCode) > 0:
                kanaCode += "A" + kanaCode[-1]
            else:
                kanaCode += "XX"
        # スペースの場合
        elif charText in "　":
            kanaCode += "WW"
        # 上記以外の場合
        else:
            # そのまま追加する
            text = kks.convert(charText)[0]["hira"]
            if kks.convert(charText)[0]["orig"] != kks.convert(charText)[0]["kana"]:
                kanaCode += convert_kana_code(text)
            else:
                kanaCode += sub(charCode, None)
    return kanaCode
