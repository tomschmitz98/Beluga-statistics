import json
import pandas as pd
import matplotlib.pyplot as plt


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


def _load_range_data(json_data: dict[str, list[dict[str, int | float | dict[str, int]]]]):
    keys = json_data.keys()
    df_dict = {"ID": [], "RSSI": [], "RANGE": [], "MAX_NOISE": [], 'FIRST_PATH_AMP1': [], 'STD_NOISE': [],
               'FIRST_PATH_AMP2': [], 'FIRST_PATH_AMP3': [], 'MAX_GROWTH_CIR': [], 'RX_PREAMBLE_CNT': [],
               'FIRST_PATH': [], 'PHE': [], 'RSL': [], 'CRCG': [], 'CRCB': [], 'ARFE': [], 'OVER': [], 'SFDTO': [],
               'PTO': [], 'RTO': [], 'TXF': [], 'HPW': [], 'TXW': []}
    for id_ in keys:
        df_dict["ID"] += [id_] * len(json_data[id_])
        for sample in json_data[id_]:
            df_dict["RSSI"] += [sample["RSSI"]]
            df_dict["RANGE"] += [sample["RANGE"]]
            for key, val in sample["UWB_DIAGNOSTICS"].items():
                df_dict[key] += [val]
            for key, val in sample["EVENTS"].items():
                df_dict[key] += [val]
    return pd.DataFrame(df_dict)


class UwbData:
    def __init__(self, fname: str):
        with open(fname, 'r') as fd:
            data = json.load(fd)

        self._df0 = _load_config_data(data["configurations"])
        self._df1 = _load_drop_data(data['drops'])
        self._df2 = _load_range_data(data['samples'])

    @property
    def configs(self) -> pd.DataFrame:
        return self._df0

    @property
    def drops(self) -> pd.DataFrame:
        return self._df1

    @property
    def samples(self) -> pd.DataFrame:
        return self._df2


if __name__ == "__main__":
    data = UwbData("test.json")
    print(data.drops)
    print(data.samples)
