import logging
import re
import requests
from bs4 import BeautifulSoup

ENCHANTER_PREFIX = ""
ENCHANTER_SUFFIX = ""
ENCHANTER_EXCLUDES = []

log = logging.getLogger(__name__)


def is_enchanter_node(node):
    return node.name == "span"


def get_display_enchanter(enchanter):
    return f"{ENCHANTER_PREFIX}{enchanter}{ENCHANTER_SUFFIX}"


def get_enchanter(node):
    r = re.match(".*「(.*)」の詳細.*", node.text)
    if r:
        return r.group(1)
    return ""


def is_enchant_node(node):
    return node.name == "table"


def get_equip_names(node):
    if len(node.select("tr:nth-child(1)>th")) != 3:
        return []
    name_node = node.select_one("tr:nth-child(2)>td:nth-child(1)")
    if name_node == None:
        return []
    text = name_node.get_text(",").strip()
    names = []
    for t in text.split(","):
        if t.strip() != "":
            names.append(t.strip())
    return names


def get_enchant_columns(table, tr):
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
    slot = get_enchant_slot(condition)
    if slot == 4:
        return 8
    elif slot == 3:
        return 9
    elif slot == 2:
        return 10
    else:
        return 0


def build_enchants(enchanter, table, equips):
    equip_names = get_equip_names(table)
    for equip_name in equip_names:
        equip = equips.get(equip_name, {"name": equip_name, "enchants": list()})
        slots = []
        for tr in table.select("tr"):
            condition_node, data_node = get_enchant_columns(table, tr)
            if condition_node is None:
                continue
            # rowspanを雑に対処
            if data_node == None:
                data_node = prev_data_node

            enchant_slot = get_enchant_slot(condition_node)
            if enchant_slot is None:
                continue
            refining = get_enchant_refining(condition_node)
            prev_data_node = data_node
            enchant_data = []
            for i in data_node.get_text("、").replace("\n", "、").split("、"):
                if i.strip() != "":
                    enchant_data.append(i.replace(" ", "").strip())
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
    r = requests.get(
        "https://ragnarokonline.gungho.jp/gameguide/system/expand-item/fides.html"
    )
    soup = BeautifulSoup(r.text, "html.parser")
    nodes = soup.select(".hl02>span, #main3column>div>div>table")
    enchanter = None

    enchlist = []
    for node in nodes:
        if is_enchanter_node(node):
            enchanter = get_enchanter(node)

        if enchanter in ENCHANTER_EXCLUDES:
            continue

        if is_enchant_node(node):
            enchlist.extend(
                build_enchants(get_display_enchanter(enchanter), node, equips)
            )
    return enchlist
