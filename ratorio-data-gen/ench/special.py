import logging
import re
import requests
from bs4 import BeautifulSoup

ENCHANTER_PREFIX = "スペシャルエンチャント（"
ENCHANTER_SUFFIX = "）"
ENCHANTER_EXCLUDES = ["ピカニャン"]
default_refining = []

log = logging.getLogger(__name__)


def is_enchanter_node(node):
    return node.name == "span"


def get_display_enchanter(enchanter):
    return f"{ENCHANTER_PREFIX}{enchanter}{ENCHANTER_SUFFIX}"


def get_enchanter(node):
    r = re.match(".*「(.*)」で可能な.*", node.text)
    if r:
        return r.group(1)
    return ""


def is_enchant_node(node):
    return node.name == "table"


def get_table_type(node):
    # 2列か3列でデータ場所が変わるので種別として扱う
    # メモクロだけ thead がないので補正
    table_type = len(node.select("thead>tr>th"))
    if table_type == 0:
        table_type = len(node.select("tbody>tr:nth-child(1)>th"))
    return table_type


def get_equip_names(node):
    table_type = get_table_type(node)
    if table_type == 2:
        name_node = node.select_one("thead>tr>th:nth-child(1)")
    elif table_type == 3:
        name_node = node.select_one("tbody>tr:nth-child(1)>td:nth-child(1)")
        if name_node is None:
            name_node = node.select_one("tbody>tr:nth-child(2)>td:nth-child(1)")
    else:
        return []

    if name_node == None:
        # 「確定・通常エンチャント」など不要なテーブル
        return []
    text = name_node.get_text(",").strip()
    # 「エンチャント手数料」や「エンチャント成功率」を雑に回避
    if not text.endswith("]"):
        return []

    names = []
    for t in text.split(","):
        names.append(t.strip())
    return names


def get_enchant_columns(table, tr):
    table_type = get_table_type(table)
    # メモクロだけヘッダ行がtbodyにいる
    if tr.select("th"):
        return (None, None)

    if table_type == 2:
        condition = tr.select_one("td:nth-child(1)")
        data = tr.select_one("td:nth-child(2)")
    else:
        condition = tr.select_one("td:nth-child(2)")
        data = tr.select_one("td:nth-child(3)")
        if data == None:
            # rowspan で nth-child の位置がずれる場合
            data = condition
            condition = tr.select_one("td:nth-child(1)")
    return (condition, data)


def get_enchant_slot(condition):
    slot = re.match("第(\\d+)エンチャント", condition.text.strip())
    if slot == None:
        slot = re.match("(\\d+)番目", condition.text.strip())
        if slot == None:
            return None
    return 5 - int(slot.group(1))


def get_enchant_refining(condition):
    refining = re.match(".*精錬値(\\d+)", condition.text.strip(), flags=re.DOTALL)
    return 0 if refining == None else int(refining.group(1))


def get_default_refining(table):
    refining = [0,0,0,0]
    for tr in table.select("tbody>tr"):
        if tr.select_one("td:nth-child(1)").text.strip() == "エンチャントに必要な対象アイテムの精錬値":
            for line in tr.select_one("td:nth-child(2)").get_text(",").replace("\n","").split(","):
                terms = line.split(":")
                r = re.match("第(\\d)～?(\\d)?スロット", terms[0].strip())
                if r :
                    min = int(r.group(1))
                    max = int(r.group(2)) if r.group(2) else min
                    r = re.match(".*精錬値(\\d+)", terms[1].strip(), flags=re.DOTALL)
                    v = 0 if r == None else int(r.group(1))
                    for slot in range(min, max+1):
                        refining[slot-1] = v
            break
    return refining

def build_enchants(enchanter, table, equips):
    equip_names = get_equip_names(table)
    for equip_name in equip_names:
        equip = equips.get(equip_name, {"name": equip_name, "enchants": list()})
        slots = []
        for tr in table.select("tbody>tr"):
            condition_node, data_node = get_enchant_columns(table, tr)
            # メモクロ ヘッダ行skip
            if condition_node is None:
                continue
            # rowspanを雑に対処
            if data_node == None:
                data_node = prev_data_node

            enchant_slot = get_enchant_slot(condition_node)
            # スロットエンチャント skip
            if enchant_slot is None:
                continue
            if default_refining:
                refining = default_refining[enchant_slot-1]
            else:
                refining = get_enchant_refining(condition_node)
            prev_data_node = data_node

            enchant_data = []
            for i in data_node.get_text("、").replace("\n", "、").split("、"):
                if i.strip() != "":
                    enchant_data.append(i.strip())
            slots.append(
                {
                    "slot": enchant_slot,
                    "refining": refining,
                    "enchants": enchant_data,
                }
            )

        equip["enchants"].append(
            {
                "enchanter": enchanter,
                "slots": slots,
            }
        )
        equips[equip_name] = equip
    if len(equip_names) > 0:
        return [
            {
                "enchanter": enchanter,
                "equips": equip_names,
                "slots": slots,
            }
        ]
    return []


def crawl(equips):
    global default_refining
    r = requests.get(
        "https://ragnarokonline.gungho.jp/gameguide/system/equip-powerup/special-enchant.html"
    )
    soup = BeautifulSoup(r.text, "html.parser")
    nodes = soup.select(".hl02>span, h4, #main3column table")
    enchanter = None

    enchlist = []
    for node in nodes:
        if is_enchanter_node(node):
            enchanter = get_enchanter(node)
            default_refining = None

        if enchanter in ENCHANTER_EXCLUDES:
            continue

        if node.name == "h4":
            default_refining = None

        if is_enchant_node(node):
            if not default_refining:
                default_refining = get_default_refining(node)
            enchlist.extend(
                build_enchants(get_display_enchanter(enchanter), node, equips)
            )

    return enchlist
