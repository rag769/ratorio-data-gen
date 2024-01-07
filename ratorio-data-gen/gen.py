import argparse
import config
import ench.clock as clock
import ench.fides as fides
import ench.pharos as pharos
import ench.special as special
import ench.star as start
import json
import os
import re
import util


def load_dat_js(file: str, obj_name: str, cb):
    dat = []
    id_by_name = {}
    with open(file) as f:
        isDat: bool = False
        for line in f.readlines():
            s = line.strip()
            if not isDat and s == f"{obj_name} = [":
                isDat = True
            elif isDat and s == "];":
                isDat = False
            elif isDat:
                try:
                    s = re.sub(",[ ]*,", ",None,", s)
                    value = eval(s[: s.rindex("],") + 1])
                    dat.append(cb(value))
                    id_by_name[cb(value)] = value[0]
                except:
                    pass
            elif (r := re.match(f"{obj_name}\[(\d+)\]", s)) is not None:
                if len(dat) <= int(r.group(1)):
                    dat.extend([None] * (int(r.group(1)) - len(dat) + 1))
                try:
                    s = re.sub(",[ ]*,", ",None,", s)
                    val = "".join(s.split("=")[1:])
                    dat[int(r.group(1))] = cb(eval(val[: val.rindex("];") + 1]))
                    id_by_name[dat[int(r.group(1))]] = int(r.group(1))
                except:
                    pass
    return dat, id_by_name


def main():
    # JS ファイルから XXXXObjNew を読む
    # js2py を試したら遅すぎた…
    items, items_by_name = load_dat_js(
        config.item_dat_path, "ItemObjNew", lambda v: v[8]
    )
    cards, cards_by_name = load_dat_js(
        config.card_dat_path, "CardObjNew", lambda v: v[2]
    )
    ench, ench_by_name = load_dat_js(
        config.ench_dat_path,
        "g_constDataManager.enchListDataManager.sourceArray",
        lambda v: f"{v[4][0][0]}:{v[6][0][0][1][1]}",
    )

    equips = {}
    enchlist = []
    enchlist.extend(special.crawl(equips))
    enchlist.extend(pharos.crawl(equips))
    enchlist.extend(fides.crawl(equips))
    enchlist.extend(clock.crawl(equips))
    # star.crawl(equips)

    lists = []
    for v in enchlist:
        ###
        # 他と命名ルールが違う
        if "王冠をつけたシナモンのリュック[0]" in v["equips"]:
            v["enchanter"] = "20周年記念ドリームコラボ"
        ###
        v["kana_code"] = (
            util.convert_kana_code(v["enchanter"]).replace("XX", "").replace("WW", "")
        )
        v["equip_codes"] = list()
        for e in v["equips"]:
            v["equip_codes"].append(util.lookup_item_dict(items_by_name, e))

        ench_id = ench_by_name.get(f'{v["enchanter"]}:{v["equip_codes"]}', "{ench_id}")
        sp = [
            [174, [50, v["equip_codes"]]],
            None,
        ]
        ench = [ench_id, -1, 0, 0, [[v["enchanter"], v["kana_code"]]], [], [sp], []]
        dat = []
        for s in v["slots"]:
            d = [[178, [27, [s["slot"]]]], None]
            for idx, val in enumerate(s["enchants"]):
                s["enchants"][idx] = util.lookup_card_dict(cards_by_name, val)
            if s["refining"] == 0:
                d.append([[[186, [51, s["enchants"]]], None, []]])
            else:
                d.append(
                    [
                        [
                            [187, [59, s["refining"]], [60, 4]],
                            None,
                            [[[186, [51, s["enchants"]]], None, []]],
                        ]
                    ]
                )
            dat.append(d)
        sp.append(dat)
        lists.append(ench)

    os.makedirs(config.dist, exist_ok=True)
    with open(os.path.join(config.dist, "enchlist.txt"), "w") as f:
        revresolve = {}
        for l in lists:
            msg = f"g_constDataManager.enchListDataManager.sourceArray[{l[0]}] = {l}\n"
            f.write(
                msg.replace("\\u3000", "　")
                .replace("None", "")
                .replace(" ", "")
                .replace("'", '"')
            )
            for i in l[6][0][0][1][1]:
                r = revresolve.get(i, [])
                r.append(l[0])
                revresolve[i] = r
        for k, v in sorted(
            revresolve.items(), key=lambda x: x[0] if type(x[0]) != str else 99999
        ):
            msg = f"(g_constDataManager.enchListDataManager.reverseResolveArrayItemId[{k}] = g_constDataManager.enchListDataManager.reverseResolveArrayItemId[{k}]||[]).push({','.join([str(i) for i in v])})\n"
            f.write(msg)

    # with open("equips.json", "w") as f:
    #     json.dump(dest, f, indent=4, ensure_ascii=False)

    # with open("enchlist.json", "w") as f:
    #     json.dump(lists, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
