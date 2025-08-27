import pandas as pd
from import_data import UwbData
import statistics
import math
from typing import Callable


class UwbStats:
    def __init__(self, data: dict[int, UwbData]):
        self._data: dict[int, UwbData] = data
        stat_data: dict[str, list[float | int | list[float]]] = {
            "range": [],
            "range_mean": [],
            "range_median": [],
            "range_stddev": [],
            "range_var": [],
            "rssi_mean": [],
            "rssi_median": [],
            "rssi_stddev": [],
            "rssi_var": [],
            "rx_pow_mean": [],
            "rx_pow_median": [],
            "rx_pow_stddev": [],
            "rx_pow_var": [],
            "rx_pow": [],
            "fp_mean": [],
            "fp_median": [],
            "fp_stddev": [],
            "fp_var": [],
            "fp": [],
            "prr": [],
            "dropped_rx": [],
            "total_rx": [],
            "mean_cir": [],
            # Add new stats to the end...
        }

        for range_, data_ in sorted(self._data.items(), key=lambda kv: kv[0]):
            stat_data["range"] += [range_]
            self._compute_range_stats(range_, stat_data)
            self._compute_rssi_states(range_, stat_data)
            self._compute_uwb_rx_power(range_, stat_data)
            self._compute_uwb_fp_power(range_, stat_data)
            self._compute_prr(range_, stat_data)
        self._stats = pd.DataFrame(stat_data)

    def log_range(self, logger: Callable[[any], None] | None):
        if logger is None:
            return
        if logger == print:
            ending = ""
        else:
            ending = "\n"
        for data in self._stats.values:
            logger(f"--- Statistics for UWB Ranging at {data[0]} meters ---{ending}")
            logger(f"Mean Range: {data[1]}{ending}")
            logger(f"Median Range: {data[2]}{ending}")
            logger(f"Range Standard Deviation: {data[3]}{ending}")
            logger(f"Range Variance: {data[4]}{ending}")
            logger(ending)

    def log_rssi(self, logger: Callable[[any], None] | None):
        if logger is None:
            return
        if logger == print:
            ending = ""
        else:
            ending = "\n"
        for data in self._stats.values:
            logger(f"--- Statistics for BLE RSSI at {data[0]} meters ---{ending}")
            logger(f"Mean RSSI: {data[5]}{ending}")
            logger(f"Median RSSI: {data[6]}{ending}")
            logger(f"RSSI Standard Deviation: {data[7]}{ending}")
            logger(f"RSSI Variance: {data[8]}{ending}")
            logger(ending)

    def log_uwb_power(self, logger: Callable[[any], None] | None):
        if logger is None:
            return
        if logger == print:
            ending = ""
        else:
            ending = "\n"
        for data in self._stats.values:
            logger(f"--- Statistics for UWB Power at {data[0]} meters ---{ending}")
            logger(f"Mean RX Power: {data[9]}{ending}")
            logger(f"Median RX Power: {data[10]}{ending}")
            logger(f"RX Power Standard Deviation: {data[11]}{ending}")
            logger(f"RX Power Variance: {data[12]}{ending}")
            logger(f"Mean First Path Power: {data[14]}{ending}")
            logger(f"Median First Path Power: {data[15]}{ending}")
            logger(f"First Path Power Standard Deviation: {data[16]}{ending}")
            logger(f"First Path Power Variance: {data[17]}{ending}")
            logger(ending)

    def log_uwb_prr(self, logger: Callable[[any], None] | None):
        if logger is None:
            return
        if logger == print:
            ending = ""
        else:
            ending = "\n"
        for data in self._stats.values:
            logger(f"--- Statistics for UWB PRR at {data[0]} meters ---{ending}")
            logger(f"Packet Reception Rate: {data[19]}{ending}")
            logger(f"Dropped Receptions: {data[20]}{ending}")
            logger(f"Total Receptions: {data[21]}{ending}")
            logger(ending)

    def _compute_range_stats(self, range_: int, stats: dict[str, float | int | list[float]]):
        stats["range_mean"] += [self._data[range_].samples["RANGE"].mean()]
        stats["range_median"] += [self._data[range_].samples["RANGE"].median()]
        stats["range_stddev"] += [self._data[range_].samples["RANGE"].std()]
        stats["range_var"] += [self._data[range_].samples["RANGE"].var()]

    def _compute_rssi_states(self, range_: int, stats: dict[str, float | int | list[float]]):
        stats["rssi_mean"] += [self._data[range_].samples["RSSI"].mean()]
        stats["rssi_median"] += [self._data[range_].samples["RSSI"].median()]
        stats["rssi_stddev"] += [self._data[range_].samples["RSSI"].std()]
        stats["rssi_var"] += [self._data[range_].samples["RSSI"].var()]

    def _compute_uwb_rx_power(self, range_: int, stats: dict[str, float | int | list[float]]):
        A = 121.74 if self._data[range_].configs["Pulse rate"][0] == 1 else 113.77
        rx_level = []
        for C, N in zip(self._data[range_].samples["MAX_GROWTH_CIR"], self._data[range_].samples["RX_PREAMBLE_CNT"]):
            if C <= 0:
                C = 1e-9
            rx_level += [(10 * math.log10((C * (2 ** 17)) / (N ** 2))) - A]
        stats["rx_pow_mean"] += [statistics.mean(rx_level)]
        stats["rx_pow_median"] += [statistics.median(rx_level)]
        stats["rx_pow_stddev"] += [statistics.stdev(rx_level)]
        stats["rx_pow_var"] += [statistics.variance(rx_level)]
        stats["rx_pow"] += [rx_level]
        stats["mean_cir"] += [self._data[range_].samples["MAX_GROWTH_CIR"].mean()]

    def _compute_uwb_fp_power(self, range_: int, stats: dict[str, float | int | list[float]]):
        A = 121.74 if self._data[range_].configs["Pulse rate"][0] == 1 else 113.77
        fp_level = []
        for F1, F2, F3, N in zip(self._data[range_].samples["FIRST_PATH_AMP1"],
                                 self._data[range_].samples["FIRST_PATH_AMP2"],
                                 self._data[range_].samples["FIRST_PATH_AMP3"],
                                 self._data[range_].samples["RX_PREAMBLE_CNT"]):
            fp_level += [(10 * math.log10(((F1 ** 2) + (F2 ** 2) + (F3 ** 2)) / (N ** 2))) - A]
        stats["fp_mean"] += [statistics.mean(fp_level)]
        stats["fp_median"] += [statistics.median(fp_level)]
        stats["fp_stddev"] += [statistics.stdev(fp_level)]
        stats["fp_var"] += [statistics.variance(fp_level)]
        stats["fp"] += [fp_level]

    def _compute_prr(self, range_: int, stats: dict[str, float | int | list[float]]):
        failed_polls: int = 0
        failed_responses: int = 0
        failed_finals: int = 0
        failed_reports: int = 0

        for stage, count in zip(self._data[range_].drops["Stage"], self._data[range_].drops["Count"]):
            match stage:
                case 0:
                    failed_polls += count
                case 1:
                    failed_responses += count
                case 2:
                    failed_finals += count
                case 3:
                    failed_reports += count

        successful_receptions = (len(self._data[range_].samples["RANGE"]) * 2) + failed_reports
        failed_receptions = failed_responses + failed_reports
        total_receptions = successful_receptions + failed_receptions

        stats["prr"] += [(1 - (failed_receptions / total_receptions)) * 100]
        stats["dropped_rx"] += [failed_receptions]
        stats["total_rx"] += [total_receptions]

    @property
    def data(self) -> dict[int, UwbData]:
        return self._data

    @property
    def stats(self) -> pd.DataFrame:
        return self._stats

    @property
    def distances(self) -> list[int]:
        return list(self._data.keys())


if __name__ == "__main__":
    _data = UwbData("test.json")
    _data = {1: _data}
    _data = UwbStats(_data)
    _data.log_range(print)
    _data.log_rssi(print)
    _data.log_uwb_power(print)
    _data.log_uwb_prr(print)
