import json
import math
import pandas as pd


def _load_config_data(json_data: dict[str, str | int | bool]) -> pd.DataFrame:
    def _extract_number(s: str, base = 10) -> int | None:
        if base == 10:
            val = [x for x in s.split() if x.isdigit()]
        elif base == 16:
            val = [x for x in s.split() if x.startswith("0x")]
        else:
            raise ValueError(f"Invalid base: {base}")
        if val:
            return int(val[0], base=base)
        return None

    json_data["ID"] = int(json_data["ID"])
    json_data["Channel"] = int(json_data["Channel"])
    json_data["Data rate"] = _extract_number(json_data["Data rate"])
    json_data["Pulse rate"] = _extract_number(json_data["Pulse rate"])
    json_data["Preamble"] = _extract_number(json_data["Preamble"])
    json_data["PAC"] = _extract_number(json_data["PAC"])
    json_data["TX Power"] = _extract_number(json_data["TX Power"], 16)
    data = {key: [val] for key, val in json_data.items()}
    return pd.DataFrame(data)


def _load_drop_data(json_data: dict[str, dict[str, dict[str, int | dict[str, int]]]]) -> pd.DataFrame:
    keys = list(json_data.keys())
    ids = []
    for id_ in keys:
        ids += [id_] * 4
    stages = [0, 1, 2, 3]
    df_dict = {
        "ID": ids,
        "Stage": stages * len(keys),
        "Count": [],
    }

    def _extract_events(events: dict[str, int]):
        for key in events.keys():
            if key not in df_dict:
                df_dict[key] = [events[key]]
            else:
                df_dict[key] += [events[key]]

    for id_ in keys:
        for stage in stages:
            df_dict["Count"] += [json_data[id_][str(stage)]['count']]
            _extract_events(json_data[id_][str(stage)]['events'])
    return pd.DataFrame(df_dict)

if __name__ == "__main__":
    with open("test.json", "r") as f:
        d = json.load(f)
    print(_load_config_data(d["configurations"]))
    print(_load_drop_data(d['drops']))
