import logging
import mojimoji
import re
import requests
from bs4 import BeautifulSoup

ENCHANTER_PREFIX = "ファロスエンチャント　"
ENCHANTER_SUFFIX = ""
ENCHANTER_EXCLUDES = []

log = logging.getLogger(__name__)


def is_enchanter_node(node):
    return node.name == "h4"


def get_display_enchanter(enchanter):
    return f"{ENCHANTER_PREFIX}{mojimoji.han_to_zen(enchanter)}{ENCHANTER_SUFFIX}"


def get_enchanter(node):
    return node.text.strip()


def is_enchant_node(node):
    return node.name == "table"


def get_equip_names(tr):
    name_node = tr.select_one("td:nth-child(2)")
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
    if tr.select_one("th:nth-child(1)"):
        condition = tr.select_one("td:nth-child(3)")
        data = tr.select_one("td:nth-child(4)")
    else:
        condition = tr.select_one("td:nth-child(1)")
        data = tr.select_one("td:nth-child(2)")
    return (condition, data)


def get_enchant_slot(condition):
    slot = re.match("第(\\d+)エンチャント", condition.text.strip())
    return 5 - int(slot.group(1))


def get_enchant_refining(condition):
    return 0


def build_enchants(enchanter, table, equips):
    enchlist = []
    for tr in table.select("tbody>tr"):
        if tr.select_one("th:nth-child(1)"):
            equip_names = get_equip_names(tr)
            slots = []
            enchant = {
                "enchanter": enchanter,
                "slots": slots,
            }
            if len(equip_names) > 0:
                enchlist.append(
                    {
                        "enchanter": enchanter,
                        "equips": equip_names,
                        "slots": slots,
                    }
                )
            for equip_name in equip_names:
                equip = equips.get(equip_name, {"name": equip_name, "enchants": list()})
                equip["enchants"].append(enchant)
                equips[equip_name] = equip

        condition_node, data_node = get_enchant_columns(table, tr)
        if condition_node is None:
            continue
        # rowspanを雑に対処
        if data_node == None:
            data_node = prev_data_node

        enchant_slot = get_enchant_slot(condition_node)
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
    return enchlist


def crawl(equips):
    r = requests.get(
        "https://ragnarokonline.gungho.jp/gameguide/system/equip-powerup/pharos-enchant.html"
    )
    soup = BeautifulSoup(r.text, "html.parser")
    nodes = soup.select("h4,.c-table.c-table--02")
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
