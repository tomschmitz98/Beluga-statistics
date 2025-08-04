import statistics
from import_data import UwbData, UwbDrops
from collections import Counter
from typing import Callable
import matplotlib.pyplot as plt
from pathlib import Path
import dataclasses
import re


SHOW_PLOTS = False


def plot_histogram(counts, x_label: str, y_label: str, title: str, reverse: bool = False):
    raw_data = []
    for value, count in counts.items():
        raw_data.extend([value] * count)
    plt.hist(raw_data, bins=range(min(raw_data), max(raw_data) + 2), align='right')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)

    if reverse:
        plt.gca().invert_xaxis()

    plt.show()


class UwbStats:
    @dataclasses.dataclass
    class BleRSSI:
        rssi_mean: float = 0.0
        rssi_median: float = 0.0
        rssi_stddev: float = 0.0
        rssi_var: float = 0.0
        rssi_count: Counter[int] | None = None

    @dataclasses.dataclass
    class UwbRange:
        range_mean: float = 0
        range_median: float = 0
        range_stddev: float = 0
        range_var: float = 0

    @dataclasses.dataclass
    class UwbRxPower:
        rx_pow_mean: float = 0
        rx_pow_median: float = 0
        rx_pow_stddev: float = 0
        rx_pow_var: float = 0
        rx_pow: list[float] = dataclasses.field(default_factory=list)

        fp_mean: float = 0
        fp_median: float = 0
        fp_stddev: float = 0
        fp_var: float = 0
        fp: list[float] = dataclasses.field(default_factory=list)

    @dataclasses.dataclass
    class UwbReceptionData:
        prr: float = 0
        dropped_rx: int = 0
        total_rx: int = 0

    def __init__(self, trial: int | None = None, data: UwbData | None = None):
        self._trial = trial
        self._data = data
        self._ble_stats: dict[str, UwbStats.BleRSSI] = {}
        self._uwb_range_stats: dict[str, UwbStats.UwbRange] = {}
        self._uwb_rx_stats: dict[str, UwbStats.UwbRxPower] = {}
        self._uwb_reception_stats: dict[str, UwbStats.UwbReceptionData] = {}
        self._mean_rssi: int = 0
        self._mean_rx_power: float = 0.0
        self._mean_prr: float = 0.0
        self._mean_cir: float = 0.0

    @property
    def trial(self):
        return self._trial

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, new: UwbData):
        self._data = new

    @property
    def ble_rssi(self):
        return self._ble_stats

    @property
    def uwb_range(self):
        return self._uwb_range_stats

    @property
    def uwb_rx_power(self):
        return self._uwb_rx_stats

    @property
    def uwb_reception(self):
        return self._uwb_reception_stats

    @property
    def mean_ble_rssi(self):
        return self._mean_rssi

    @property
    def mean_uwb_rx_power(self):
        return self._mean_rx_power

    @property
    def mean_prr(self):
        return self._mean_prr

    @property
    def mean_cir(self):
        return self._mean_cir

    def update_mean_rssi(self):
        samples = self._data.samples
        rssi = []
        for id_ in self._data.other_nodes:
            rssi += samples[id_].rssi
        self._mean_rssi = round(statistics.mean(rssi))

    def update_mean_uwb_rx_power(self):
        samples = self._data.samples
        uwb_rx_pow = []
        for id_ in self._data.other_nodes:
            uwb_rx_pow += samples[id_].uwb_rx_power
        self._mean_rx_power = statistics.mean(uwb_rx_pow)

    def update_mean_uwb_cir(self):
        samples = self._data.samples
        uwb_cir = []
        for id_ in self._data.other_nodes:
            uwb_cir += [diagnostics["MAX_GROWTH_CIR"] for diagnostics in samples[id_].uwb_diagnostic_info]
        self._mean_cir = statistics.mean(uwb_cir)

    def update_uwb_prr(self):
        total_drops: int = 0
        total_rx: int = 0
        for id_ in self._data.other_nodes:
            total_drops += self._uwb_reception_stats[id_].dropped_rx
            total_rx += self._uwb_reception_stats[id_].total_rx
        self._mean_prr = (1 - (total_drops / total_rx)) * 100

    @property
    def all_ble_rssi(self):
        rssi = []
        for sample in self._data.samples.values():
            rssi += sample.rssi
        return rssi

    @property
    def all_uwb_rx_power(self):
        rx_pow = []
        for sample in self._data.samples.values():
            rx_pow += sample.uwb_rx_power
        return rx_pow

    @property
    def all_uwb_reception(self):
        drops: list[UwbDrops] = []
        for sample in self._data.drops.values():
            drops.append(sample)
        return drops

    @property
    def all_uwb_cir(self):
        cir = []
        for sample in self._data.samples.values():
            cir += sample.uwb_diagnostic_info["MAX_GROWTH_CIR"]
        return cir

    @property
    def all_uwb_ranges(self):
        ranges = []
        for sample in self._data.samples.values():
            ranges += sample.range
        return ranges

class UwbDataProcessing:
    def __init__(self, node: int):
        self._folder: Path = Path(f"data/Node {node}")
        self._data: dict[int, list[UwbStats]] = {}
        for f in self._folder.glob("*.json"):
            distance, trial = self._extract_distance(f.name)
            if distance not in self._data:
                self._data[distance] = [UwbStats(trial=trial, data=UwbData(f))]
            else:
                self._data[distance].append(UwbStats(trial=trial, data=UwbData(f)))
        self._rssi_stats()
        self._uwb_stats()

    @staticmethod
    def _extract_distance(name) -> tuple[int, int | None]:
        regex = re.compile(f'\d+')
        numbers = [int(x) for x in regex.findall(name)]
        if not numbers:
            raise ValueError("Improperly named file")
        if len(numbers) == 1:
            return numbers[0], None
        return numbers[0], numbers[1]

    @staticmethod
    def __rssi_stats(data_set: UwbStats):
        samples = data_set.data.samples
        for id_ in data_set.data.other_nodes:
            rssi = samples[id_].rssi
            data = UwbStats.BleRSSI()
            data.rssi_mean = statistics.mean(rssi)
            data.rssi_median = statistics.median(rssi)
            data.rssi_stddev = statistics.stdev(rssi)
            data.rssi_var = statistics.variance(rssi)
            data.rssi_count = Counter(rssi)
            data_set.ble_rssi[id_] = data

    def _rssi_stats(self):
        for distance, stats in self._data.items():
            for data_set in stats:
                self.__rssi_stats(data_set)
                data_set.update_mean_rssi()

    @staticmethod
    def _uwb_prr(data: UwbDrops):
        drop_rate = data.dropped_receptions() / data.total_receptions()
        return (1 - drop_rate) * 100

    def _uwb_reception(self, data_set: UwbStats):
        drop_data = data_set.data.drops
        for id_ in data_set.data.other_nodes:
            drops = drop_data[id_]
            data = UwbStats.UwbReceptionData()
            data.prr = self._uwb_prr(drops)
            data.dropped_rx = drops.dropped_receptions()
            data.total_rx = drops.total_receptions()
            data_set.uwb_reception[id_] = data

    @staticmethod
    def __uwb_stats(data_set: UwbStats):
        samples = data_set.data.samples
        for id_ in data_set.data.other_nodes:
            ranges = samples[id_].range
            data = UwbStats.UwbRange()
            data.range_mean = statistics.mean(ranges)
            data.range_median = statistics.median(ranges)
            data.range_stddev = statistics.stdev(ranges)
            data.range_var = statistics.variance(ranges)
            data_set.uwb_range[id_] = data

    @staticmethod
    def _uwb_rx_power(data_set: UwbStats):
        samples = data_set.data.samples
        for id_ in data_set.data.other_nodes:
            rx_pow = samples[id_].uwb_rx_power
            fp_pow = samples[id_].uwb_signal_power_in_first_path
            data = UwbStats.UwbRxPower()
            data.rx_pow_mean = statistics.mean(rx_pow)
            data.rx_pow_median = statistics.median(rx_pow)
            data.rx_pow_stddev = statistics.stdev(rx_pow)
            data.rx_pow_var = statistics.variance(rx_pow)
            data.rx_pow = rx_pow
            data.fp_mean = statistics.mean(fp_pow)
            data.fp_median = statistics.median(fp_pow)
            data.fp_stddev = statistics.stdev(fp_pow)
            data.fp_var = statistics.variance(fp_pow)
            data.fp = fp_pow
            data_set.uwb_rx_power[id_] = data

    def _uwb_stats(self):
        for distance, stats in self._data.items():
            for data_set in stats:
                self.__uwb_stats(data_set)
                self._uwb_reception(data_set)
                self._uwb_rx_power(data_set)
                data_set.update_mean_uwb_rx_power()
                data_set.update_uwb_prr()
                data_set.update_mean_uwb_cir()

    @staticmethod
    def _print_rssi_stats(callback: Callable[[any], None], data: UwbStats, title_fmt: str):
        if callback == print:
            ending = ""
        else:
            ending = "\n"
        for id_, ble_data in data.ble_rssi.items():
            callback(title_fmt % id_)
            callback(f"RSSI Mean: {ble_data.rssi_mean}{ending}")
            callback(f"RSSI Median: {ble_data.rssi_median}{ending}")
            callback(f"RSSI Standard Deviation: {ble_data.rssi_stddev}{ending}")
            callback(f"RSSI Variance: {ble_data.rssi_var}{ending}")

    def print_rssi_stats(self, callback: Callable[[any], None] = print):
        if callback == print:
            ending = ""
        else:
            ending = "\n"
        for distance, stats in self._data.items():
            callback(f"--- Statistics for BLE RSSI at {distance} meters ---{ending}")
            if len(stats) == 1:
                self._print_rssi_stats(callback, stats[0], f"Node ID: %s{ending}")
            else:
                for trial in stats:
                    self._print_rssi_stats(callback, trial, f"<<< Node ID: %s, Trial {trial.trial} >>>{ending}")
        callback(f"\n{ending}")

    @staticmethod
    def _plot_rssi_single(counts: Counter[int], title: str, distance: int, save_dir: Path | None):
        x = list(counts.keys())
        x.sort()
        x_labels = [str(i) for i in x]
        y = []
        for i in x_labels:
            y.append(counts[int(i)])

        width = max(6.4, len(x) * 0.6)

        fig, axis = plt.subplots(figsize=(width, 4.8))

        axis.bar(x_labels, y, align='center')
        axis.invert_xaxis()

        axis.set_xlabel("RSSI")
        axis.set_ylabel("Frequency (Occurrences)")
        axis.set_title(title)
        fig.tight_layout()

        if save_dir is not None:
            fname = save_dir / f"rssi_{distance}m.png"
            fig.savefig(fname)

    @staticmethod
    def _plot_rssi_v_distance(data: dict[int, int], save_dir: Path | None):
        base = -100
        x = list(data.keys())
        x.sort()
        x_labels = [str(i) for i in x]
        y = []
        for i in x_labels:
            y.append(data[int(i)] - base)

        fig, axis = plt.subplots()
        bars = axis.bar(x_labels, y, align='center', width=1.0, bottom=base)

        for bar in bars:
            yval = bar.get_height() + base
            axis.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, f"{yval}", ha='center', va='bottom', rotation=45)

        axis.set_yticks(range(base, 0, 10))

        axis.set_xlabel("Distance (m)")
        axis.set_ylabel("RSSI (dBm)")
        axis.set_title("Average RSSI at Distances")

        if save_dir is not None:
            fname = save_dir / "distance_v_rssi.png"
            fig.savefig(fname)

    def plot_rssi(self, save_dir: Path | None = None):
        data: dict[int, int] = {}
        for distance, stats in self._data.items():
            rssi = []
            mean_rssi = None
            for trial in stats:
                if trial.trial is None:
                    title = f"Node %s RSSI at {distance}m"
                    mean_rssi = trial.mean_ble_rssi
                else:
                    title = f"Node %s RSSI at {distance}m (Trial {trial.trial})"
                    rssi += trial.all_ble_rssi
                    mean_rssi = round(statistics.mean(rssi))
                for id_, rssi_data in trial.ble_rssi.items():
                    self._plot_rssi_single(rssi_data.rssi_count, title % id_, distance, save_dir)
            if mean_rssi is not None:
                data[distance] = mean_rssi
        self._plot_rssi_v_distance(data, save_dir)

    @staticmethod
    def _print_uwb_rx_power_stats(callback: Callable[[any], None], data: UwbStats, title_fmt: str):
        if callback == print:
            ending = ""
        else:
            ending = "\n"
        for id_, uwb_data in data.uwb_rx_power.items():
            callback(title_fmt % id_)
            callback(f"Mean RX Power: {uwb_data.rx_pow_mean} dBm{ending}")
            callback(f"Median RX Power: {uwb_data.rx_pow_median} dBm{ending}")
            callback(f"RX Power Standard Deviation: {uwb_data.rx_pow_stddev} dBm{ending}")
            callback(f"RX Power Variance: {uwb_data.rx_pow_var} dBm{ending}")

    @staticmethod
    def _print_uwb_fp_sig_pow_stats(callback: Callable[[any], None], data: UwbStats, title_fmt: str):
        if callback == print:
            ending = ""
        else:
            ending = "\n"
        for id_, uwb_data in data.uwb_rx_power.items():
            callback(title_fmt % id_)
            callback(f"Mean First Path Power: {uwb_data.fp_mean} dBm{ending}")
            callback(f"Median First Path Power: {uwb_data.fp_median} dBm{ending}")
            callback(f"First Path Power Standard Deviation: {uwb_data.fp_stddev} dBm{ending}")
            callback(f"First Path Power Variance: {uwb_data.fp_var} dBm{ending}")

    def print_uwb_rx_power_stats(self, callback: Callable[[any], None] = print):
        if callback == print:
            ending = ""
        else:
            ending = "\n"
        for distance, stats in self._data.items():
            callback(f"--- Statistics for UWB RX Power at {distance} meters ---{ending}")
            if len(stats) == 1:
                self._print_uwb_rx_power_stats(callback, stats[0], f"Node ID: %s{ending}")
            else:
                for trial in stats:
                    self._print_uwb_rx_power_stats(callback, trial, f"<<< Node ID: %s, Trial {trial.trial} >>>{ending}")
        callback(f"\n{ending}")
        for distance, stats in self._data.items():
            callback(f"--- Statistics for UWB First Path Power at {distance} meters ---{ending}")
            if len(stats) == 1:
                self._print_uwb_fp_sig_pow_stats(callback, stats[0], f"Node ID: %s{ending}")
            else:
                for trial in stats:
                    self._print_uwb_fp_sig_pow_stats(callback, trial, f"<<< Node ID: %s, Trial {trial.trial} >>>{ending}")
        callback(f"\n{ending}")

    @staticmethod
    def _print_ranging_stats(callback: Callable[[any], None], data: UwbStats, title_fmt: str):
        if callback == print:
            ending = ""
        else:
            ending = "\n"
        for id_, uwb_data in data.uwb_range.items():
            callback(title_fmt % id_)
            callback(f"Mean Range: {uwb_data.range_mean}{ending}")
            callback(f"Median Range: {uwb_data.range_median}{ending}")
            callback(f"Range Standard Deviation: {uwb_data.range_stddev}{ending}")
            callback(f"Range Variance: {uwb_data.range_var}{ending}")

    def print_ranging_stats(self, callback: Callable[[any], None] = print):
        if callback == print:
            ending = ""
        else:
            ending = "\n"
        for distance, stats in self._data.items():
            callback(f"--- Statistics for UWB Ranging at {distance} meters ---{ending}")
            if len(stats) == 1:
                self._print_ranging_stats(callback, stats[0], f"Node ID: %s{ending}")
            else:
                for trial in stats:
                    self._print_ranging_stats(callback, trial, f"<<< Node ID: %s, Trial {trial.trial} >>>{ending}")
        callback(f"\n{ending}")

    @staticmethod
    def _print_uwb_stats(callback: Callable[[any], None], data: UwbStats, title_fmt: str):
        if callback == print:
            ending = ""
        else:
            ending = "\n"
        for id_, uwb_data in data.uwb_reception.items():
            callback(title_fmt % id_)
            callback(f"Packet Reception Rate {uwb_data.prr:.2f}%{ending}")

    def print_uwb_stats(self, callback: Callable[[any], None] = print):
        if callback == print:
            ending = ""
        else:
            ending = "\n"
        for distance, stats in self._data.items():
            callback(f"--- Statistics for UWB Reception at {distance} meters ---{ending}")
            if len(stats) == 1:
                self._print_uwb_stats(callback, stats[0], f"Node ID: %s{ending}")
            else:
                for trial in stats:
                    self._print_uwb_stats(callback, trial, f"<<< Node ID: %s, Trial {trial.trial} >>>{ending}")
            callback(f"\n{ending}")

    @staticmethod
    def plot_uwb_rx_power_v_distance(data: dict[int, float], save_dir: Path | None):
        base = -105
        x = list(data.keys())
        x.sort()
        x_labels = [str(i) for i in x]
        y = []
        for i in x_labels:
            y.append(data[int(i)] - base)

        fig, axis = plt.subplots()
        bars = axis.bar(x_labels, y, align='center', width=1.0, bottom=base)

        for bar in bars:
            yval = bar.get_height() + base
            axis.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, f"{yval:.2f}", ha='center', va='bottom', rotation=45)

        axis.set_yticks(range(base, 0, 10))

        axis.set_xlabel("Distance (m)")
        axis.set_ylabel("UWB Received Signal Power (dBm)")
        axis.set_title("Average UWB Received Signal Power at Distances")

        if save_dir is not None:
            fname = save_dir / "distance_v_uwb_rx_power.png"
            fig.savefig(fname)

    def plot_uwb_rx_power(self, save_dir: Path | None = None):
        data: dict[int, float] = {}
        for distance, stats in self._data.items():
            rx_pow = []
            mean_rx_pow = None
            for trial in stats:
                if trial.trial is None:
                    mean_rx_pow = trial.mean_uwb_rx_power
                else:
                    rx_pow += trial.all_uwb_rx_power
                    mean_rx_pow = statistics.mean(rx_pow)
            if mean_rx_pow is not None:
                data[distance] = mean_rx_pow
        self.plot_uwb_rx_power_v_distance(data, save_dir)

    @staticmethod
    def plot_uwb_prr_v_distance(data: dict[int, float], save_dir: Path | None):
        base = 0
        x = list(data.keys())
        x.sort()
        x_labels = [str(i) for i in x]
        y = []
        for i in x_labels:
            y.append(data[int(i)] - base)

        fig, axis = plt.subplots()
        bars = axis.bar(x_labels, y, align='center', width=1.0, bottom=base)

        for bar in bars:
            yval = bar.get_height() + base
            axis.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, f"{yval:.1f}", ha='center', va='bottom', rotation=45)

        axis.set_yticks([i for i in range(base, 110, 10)])

        axis.set_xlabel("Distance (m)")
        axis.set_ylabel("UWB Packet Reception Rate (%)")
        axis.set_title("UWB Packet Reception Rate at Distances")

        if save_dir is not None:
            fname = save_dir / "distance_v_prr.png"
            fig.savefig(fname)

    def plot_uwb_prr(self, save_dir: Path | None = None):
        data: dict[int, float] = {}
        for distance, stats in self._data.items():
            all_prr: list[UwbDrops] = []
            mean_prr = None
            for trial in stats:
                if trial.trial is None:
                    mean_prr = trial.mean_prr
                else:
                    all_prr += trial.all_uwb_reception

            if all_prr:
                total_drops = sum([prr_stats.dropped_receptions() for prr_stats in all_prr])
                total_receptions = sum([prr_stats.total_receptions() for prr_stats in all_prr])
                mean_prr = (1 - (total_drops / total_receptions)) * 100
            if mean_prr is not None:
                data[distance] = mean_prr
        self.plot_uwb_prr_v_distance(data, save_dir)

    @staticmethod
    def plot_cir_v_distance(data: dict[int, float], save_dir: Path | None):
        base = 0
        x = list(data.keys())
        x.sort()
        x_labels = [str(i) for i in x]
        y = []
        for i in x_labels:
            y.append(data[int(i)] - base)

        fig, axis = plt.subplots()
        bars = axis.bar(x_labels, y, align='center', width=1.0, bottom=base)

        for bar in bars:
            yval = bar.get_height() + base
            axis.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, f"{yval:.1f}", ha='center', va='bottom', rotation=45)

        axis.set_xlabel("Distance (m)")
        axis.set_ylabel("UWB Max Growth CIR")
        axis.set_title("UWB Max Growth CIR at Distance")

        if save_dir is not None:
            fname = save_dir / "distance_v_cir.png"
            fig.savefig(fname)

    def plot_uwb_cir(self, save_dir: Path | None = None):
        data: dict[int, float] = {}
        for distance, stats in self._data.items():
            all_cir = []
            mean_cir = None
            for trial in stats:
                if trial.trial is None:
                    mean_cir = trial.mean_cir
                else:
                    all_cir += trial.all_uwb_cir
                    mean_cir = statistics.mean(all_cir)
            if mean_cir is not None:
                data[distance] = mean_cir
        self.plot_cir_v_distance(data, save_dir)

    @staticmethod
    def plot_meas_dist_v_distance(data: dict[int, float], save_dir: Path | None):
        x = sorted(list(data.keys()))
        y_experiment = [data[i] for i in x]

        fig, ax = plt.subplots()
        ax.plot(x, x, label="Actual Distance")
        ax.plot(x, y_experiment, label="Measured Distance")

        ax.set_xlabel("Theoretical Distance (m)")
        ax.set_ylabel("Measured Range (m)")
        ax.set_title("UWB Measured Distance at Distance")
        ax.grid(True)
        ax.legend()

        if save_dir is not None:
            fname = save_dir / "distance_v_measured_dist.png"
            fig.savefig(fname)

    @staticmethod
    def plot_dist_rel_err_v_distance(data: dict[int, float], stddev_data: dict[int, float], save_dir: Path | None):
        x = sorted(list(data.keys()))
        y = [data[i] for i in x]

        x_stddev = sorted(list(data.keys()))
        y_stddev = [stddev_data[i] for i in x_stddev]

        fig, ax = plt.subplots(nrows=2)
        ax[0].plot(x, y)
        ax[1].plot(x_stddev, y_stddev)

        ax[0].set_xlabel("Distance (m)")
        ax[0].set_ylabel("Relative error")
        ax[0].set_title("Measurement Relative Error at Distance")
        ax[0].grid(True)

        ax[1].set_xlabel("Distance (m)")
        ax[1].set_ylabel("Standard deviation (m)")
        ax[1].set_title("Measurement Relative Error Standard Deviation at Distance")
        ax[1].grid(True)

        plt.tight_layout()

        if save_dir is not None:
            fname = save_dir / "distance_v_meas_rel_err.png"
            fig.savefig(fname)

    @staticmethod
    def plot_dist_abs_err_v_distance(data: dict[int, float], stddev_data: dict[int, float], save_dir: Path | None):
        x = sorted(list(data.keys()))
        y = [data[i] for i in x]

        x_stddev = sorted(list(data.keys()))
        y_stddev = [stddev_data[i] for i in x_stddev]

        fig, ax = plt.subplots(nrows=2)
        ax[0].plot(x, y)
        ax[1].plot(x_stddev, y_stddev)

        ax[0].set_xlabel("Distance (m)")
        ax[0].set_ylabel("Absolute error (m)")
        ax[0].set_title("Measurement Absolute Error at Distance")
        ax[0].grid(True)

        ax[1].set_xlabel("Distance (m)")
        ax[1].set_ylabel("Standard deviation (m)")
        ax[1].set_title("Measurement Relative Error Standard Deviation at Distance")
        ax[1].grid(True)

        plt.tight_layout()

        if save_dir is not None:
            fname = save_dir / "distance_v_meas_abs_err.png"
            fig.savefig(fname)

    def plot_distance_error(self, save_dir: Path | None = None):
        data: dict[int, float] = {}
        std_dev: dict[int, float] = {}
        rel_err: dict[int, float] = {}
        abs_err: dict[int, float] = {}
        for distance, stats in self._data.items():
            all_dist = []
            mean_dist = None
            for trial in stats:
                if trial.trial is None:
                    for _, _data in trial.uwb_range.items():
                        mean_dist = _data.range_mean
                else:
                    all_dist += trial.all_uwb_ranges
                    mean_dist = statistics.mean(all_dist)
                std_dev[distance] = trial.uwb_range['101'].range_stddev
            if mean_dist is not None:
                data[distance] = mean_dist
                abs_err[distance] = abs(mean_dist - distance)
                rel_err[distance] = abs((mean_dist - distance) / distance)

        self.plot_meas_dist_v_distance(data, save_dir)
        self.plot_dist_rel_err_v_distance(rel_err, std_dev, save_dir)
        self.plot_dist_abs_err_v_distance(abs_err, std_dev, save_dir)

    @staticmethod
    def plot_rx_fp_diff_v_distance(data: dict[int, float], save_dir: Path | None):
        x = sorted(list(data.keys()))
        y = [data[i] for i in x]

        fig, ax = plt.subplots()
        ax.plot(x, y)

        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("RX_POWER - FP_POWER (dB)")
        ax.set_title("Difference between RX Power and First Path Power at Distance")
        ax.grid(True)
        ax.hlines(6, x[0], x[-1], label="LOS", colors='green', linestyles='dashed')
        ax.hlines(10, x[0], x[-1], label="NLOS", colors='red', linestyles='dashed')
        ax.legend()

        if save_dir is not None:
            fname = save_dir / "distance_v_rx_pow_fp_diff.png"
            fig.savefig(fname)

    @staticmethod
    def plot_rx_fp_diff_hist(distance: int, rx_pow: list[float], fp_pow: list[float], save_dir: Path | None):
        rx_fp_diff = []
        above_6 = 0
        for rx, fp in zip(rx_pow, fp_pow):
            diff = rx - fp
            rx_fp_diff.append(diff)
            if diff > 6:
                above_6 += 1

        print(f"Garbage measurements at {distance}m: {above_6}")

        bins = list(range(0, 20))

        fig, ax = plt.subplots()
        ax.hist(rx_fp_diff, bins)

        ax.set_xlabel("RX_POWER - FP_POWER (dB)")
        ax.set_ylabel("Occurrences")
        ax.set_xticks(bins)
        ax.set_title(f"RX Power and First Path Power Differences at {distance} m")

        ymin, ymax = ax.get_ylim()
        ax.vlines(6, ymin, ymax, label="LOS", colors='green', linestyles='dashed')
        ax.vlines(10, ymin, ymax, label="NLOS", colors='red', linestyles='dashed')
        ax.legend()

        if save_dir is not None:
            fname = save_dir / f"rx-fp_hist_{distance}m.png"
            fig.savefig(fname)
            plt.close()

    def plot_uwb_rx_power_fp_power(self, save_dir: Path | None = None):
        data: dict[int, float] = {}
        for distance, stats in self._data.items():
            all_rx_pow = []
            all_fp_pow = []
            mean_diff = None
            for trial in stats:
                if trial.trial is None:
                    for _, _data in trial.uwb_rx_power.items():
                        mean_diff = _data.rx_pow_mean - _data.fp_mean
                        all_rx_pow += _data.rx_pow
                        all_fp_pow += _data.fp
                else:
                    pass
            if mean_diff is not None:
                data[distance] = mean_diff
            if all_fp_pow and all_rx_pow:
                self.plot_rx_fp_diff_hist(distance, all_rx_pow, all_fp_pow, save_dir)
        self.plot_rx_fp_diff_v_distance(data, save_dir)

    @staticmethod
    def _plot_distance_hist(distance: int, data: list[float], save_dir: Path | None):
        fig, ax = plt.subplots()
        bins = list(range(0, 110, 10))

        bad_dist = 0
        for dist in data:
            if dist < (distance - 1):
                bad_dist += 1

        print(f"Garbage distance measurements at {distance} m: {bad_dist}")

        ax.hist(data, bins)
        ax.set_xticks(bins)
        ax.set_xlabel("Measured Distances (m)")
        ax.set_title(f"Measured Distances at {distance}m")

        if save_dir is not None:
            fname = save_dir / f"measured_distance_hist_{distance}m.png"
            fig.savefig(fname)
            plt.close()

    def plot_distance_hist(self, save_dir: Path | None = None):
        for distance, stats in self._data.items():
            for trial in stats:
                for samples in trial.data.samples.values():
                    self._plot_distance_hist(distance, samples.range, save_dir)

    @staticmethod
    def show_plots():
        plt.show()


def collect_data_naming() -> list[int]:
    data_dir = Path("./data")
    ret: list[int] = [int(str(x.stem).split()[-1]) for x in data_dir.iterdir()]
    return ret

def create_dir(node: int) -> Path:
    dir_name = f"Node {node}"
    dir_ = Path(f"./results/{dir_name}")
    dir_.mkdir(exist_ok=True)
    return dir_

def main(show_plots: bool = False):
    nodes = collect_data_naming()

    for node in nodes:
        dir_ = create_dir(node)
        data = UwbDataProcessing(node)
        with open(dir_ / "rssi.log", "w") as rssi_log:
            data.print_rssi_stats(rssi_log.write)
        with open(dir_ / "ranging.log", "w") as ranging_log:
            data.print_ranging_stats(ranging_log.write)
        with open(dir_ / "rx_power.log", "w") as power_log:
            data.print_uwb_rx_power_stats(power_log.write)
        with open(dir_ / "uwb_stats.log", "w") as stats_log:
            data.print_uwb_stats(stats_log.write)
        data.plot_rssi(dir_)
        data.plot_uwb_prr(dir_)
        data.plot_uwb_rx_power(dir_)
        data.plot_uwb_cir(dir_)
        data.plot_distance_error(dir_)
        data.plot_uwb_rx_power_fp_power(dir_)
        data.plot_distance_hist(dir_)
        if show_plots:
            data.show_plots()

if __name__ == "__main__":
    main(SHOW_PLOTS)
