import logging
import re
import requests
from bs4 import BeautifulSoup

ENCHANTER_PREFIX = "アルデバラン時計塔地下未知の空間　"
ENCHANTER_SUFFIX = ""
ENCHANTER_EXCLUDES = []

log = logging.getLogger(__name__)


def is_enchanter_node(node):
    return node.name == "h4"


def get_display_enchanter(enchanter):
    return f"{ENCHANTER_PREFIX}{enchanter}{ENCHANTER_SUFFIX}"


def get_enchanter(node):
    return node.text.strip()


def is_enchant_node(node):
    return node.name == "table"


def get_equip_names(node):
    if len(node.select("tr:nth-child(1)>th")) != 5:
        return []
    name_node = node.select_one("tr:nth-child(2)>td:nth-child(2)")
    if name_node == None:
        return []
    text = name_node.get_text("、").strip()
    if not text.endswith("]"):
        return []
    names = []
    for t in text.split("、"):
        if t.strip() != "":
            names.append(t.strip())
    return names


def get_enchant_columns(table, tr):
    slot = tr.select_one("td:nth-child(3)")
    refining = tr.select_one("td:nth-child(4)")
    data = tr.select_one("td:nth-child(5)")
    if data == None:
        slot = tr.select_one("td:nth-child(1)")
        refining = tr.select_one("td:nth-child(2)")
        data = tr.select_one("td:nth-child(3)")
    return (slot, refining, data)


def get_enchant_slot(condition):
    slot = re.match("第(\\d+)エンチャント", condition.text.strip())
    if slot == None:
        slot = re.match("(\\d+)番目", condition.text.strip())
        if slot == None:
            return None
    return 5 - int(slot.group(1))


def get_enchant_refining(refinig):
    r = re.match("(\d+).*", refinig.text.strip())
    return 0 if r == None else int(r.group(1))


def build_enchants(enchanter, table, equips):
    equip_names = get_equip_names(table)
    for equip_name in equip_names:
        equip = equips.get(equip_name, {"name": equip_name, "enchants": list()})
        slots = []
        for tr in table.select("tr"):
            slot_node, refining_node, data_node = get_enchant_columns(table, tr)
            if slot_node is None:
                continue
            # rowspanを雑に対処
            if data_node == None:
                data_node = prev_data_node

            enchant_slot = get_enchant_slot(slot_node)
            if enchant_slot is None:
                continue
            refining = get_enchant_refining(refining_node)
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
        "https://ragnarokonline.gungho.jp/gameguide/system/expand-item/clock-tower-unknown-space.html"
    )
    soup = BeautifulSoup(r.text, "html.parser")
    nodes = soup.select("h4, #main3column>div>table")
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
