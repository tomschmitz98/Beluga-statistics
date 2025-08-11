import matplotlib.pyplot as plt
import dataclasses
from pathlib import Path
from import_data import UwbData
from process_data import UwbStats


@dataclasses.dataclass
class GraphEnable:
    cir: bool = True
    ranging_err: bool = True
    distance: bool = True
    prr: bool = True
    rssi: bool = True
    rx_pow: bool = True
    fp_pow: bool = True
    rx_fp_diff: bool = True


class DataRepresentation:
    def __init__(self, stats: UwbStats, show: bool = True, enable: GraphEnable = GraphEnable(), save_dir: Path | None = None):
        self._stats = stats
        self._enable = enable
        self._show = show
        self._save_dir = save_dir

    def _plot_avg_rssi(self):
        base = -100
        x = self._stats.distances
        x.sort()
        x_labels = [str(i) for i in x]
        y = [self._stats.stats.loc[distance, 'rssi_mean'] - base for distance in x]

        fig, ax = plt.subplots()
        bars = ax.bar(x_labels, y, align='center', width=1.0, bottom=base)

        for bar in bars:
            yval = bar.get_height() + base
            ax.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, f"{yval:.2f}", ha='center', va='bottom', rotation=45)

        ax.set_yticks(range(base, 0, 10))

        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("RSSI (dBm)")
        ax.set_title("Average RSSI at Distances")

        if self._save_dir is not None:
            fname = self._save_dir / "distance_v_rssi.png"
            fig.savefig(fname)

    def _plot_avg_cir(self):
        base = 0
        x = self._stats.distances
        x.sort()
        x_labels = [str(i) for i in x]
        y = [self._stats.stats.loc[distance, 'mean_cir'] - base for distance in x]

        fig, ax = plt.subplots()
        bars = ax.bar(x_labels, y, align='center', width=1.0, bottom=base)

        for bar in bars:
            yval = bar.get_height() + base
            ax.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, f"{yval:.1f}", ha='center', va='bottom', rotation=45)

        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("UWB Max Growth CIR")
        ax.set_title("UWB Max Growth CIR at Distance")

        if self._save_dir is not None:
            fname = self._save_dir / "distance_v_cir.png"
            fig.savefig(fname)

    def _plot_distance_absolute_error(self):
        x = sorted(self._stats.distances)
        y = [abs(self._stats.stats.loc[distance, 'range_mean'] - distance) for distance in x]
        stddev_y = [self._stats.stats.loc[distance, 'range_stddev'] for distance in x]

        fig, ax = plt.subplots(nrows=2)
        ax[0].plot(x, y)
        ax[1].plot(x, stddev_y)

        ax[0].set_xlabel("Distance (m)")
        ax[0].set_ylabel("Absolute error (m)")
        ax[0].set_title("Measurement Absolute Error at Distance")
        ax[0].grid(True)

        ax[1].set_xlabel("Distance (m)")
        ax[1].set_ylabel("Standard deviation (m)")
        ax[1].set_title("Measurement Relative Error Standard Deviation at Distance")
        ax[1].grid(True)

        plt.tight_layout()

        if self._save_dir is not None:
            fname = self._save_dir / "distance_v_meas_abs_err.png"
            fig.savefig(fname)

    def _plot_distance_relative_error(self):
        x = sorted(self._stats.distances)
        y = [(abs(self._stats.stats.loc[distance, 'range_mean'] - distance) / distance) for distance in x]
        stddev_y = [self._stats.stats.loc[distance, 'range_stddev'] for distance in x]

        fig, ax = plt.subplots(nrows=2)
        ax[0].plot(x, y)
        ax[1].plot(x, stddev_y)

        ax[0].set_xlabel("Distance (m)")
        ax[0].set_ylabel("Relative error (m)")
        ax[0].set_title("Measurement Relative Error at Distance")
        ax[0].grid(True)

        ax[1].set_xlabel("Distance (m)")
        ax[1].set_ylabel("Standard deviation (m)")
        ax[1].set_title("Measurement Relative Error Standard Deviation at Distance")
        ax[1].grid(True)

        plt.tight_layout()

        if self._save_dir is not None:
            fname = self._save_dir / "distance_v_meas_abs_err.png"
            fig.savefig(fname)

    def _plot_experiment_distance(self):
        x = sorted(self._stats.distances)
        y = [self._stats.stats.loc[distance, 'range_mean'] for distance in x]

        fig, ax = plt.subplots()
        ax.plot(x, x, label="Actual distance")
        ax.plot(x, y, label="Measured distance")

        ax.set_xlabel("Theoretical Distance (m)")
        ax.set_ylabel("Measured Range (m)")
        ax.set_title("UWB Measured Distance at Distance")
        ax.grid(True)
        ax.legend()

        if self._save_dir is not None:
            fname = self._save_dir / "distance_v_measured_dist.png"
            fig.savefig(fname)

    def _plot_prr(self):
        base = 0
        x = sorted(self._stats.distances)
        y = [self._stats.stats.loc[distance, 'prr'] - base for distance in x]

        fig, ax = plt.subplots()
        bars = ax.bar([str(i) for i in x], y, align='center', width=1.0, bottom=base)

        for bar in bars:
            yval = bar.get_height() + base
            ax.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, f"{yval:.1f}", ha='center', va='bottom', rotation=45)

        ax.set_yticks([i for i in range(base, 110, 10)])

        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("UWB Packet Reception Rate (%)")
        ax.set_title("UWB Packet Reception Rate at Distances")

        if self._save_dir is not None:
            fname = self._save_dir / "distance_v_prr.png"
            fig.savefig(fname)

    def plot(self):
        self._stats.stats.set_index('range', inplace=True)
        if self._enable.rssi:
            self._plot_avg_rssi()

        if self._enable.cir:
            self._plot_avg_cir()

        if self._enable.ranging_err:
            self._plot_distance_absolute_error()
            self._plot_distance_relative_error()
            self._plot_experiment_distance()

        if self._enable.prr:
            self._plot_prr()

        if self._show:
            plt.show()


if __name__ == "__main__":
    d = {
        10: UwbData("data/Node 100/10m.json"),
        20: UwbData("data/Node 100/20m.json"),
        30: UwbData("data/Node 100/30m.json"),
        40: UwbData("data/Node 100/40m.json"),
        50: UwbData("data/Node 100/50m.json"),
        60: UwbData("data/Node 100/60m.json"),
    }
    s = UwbStats(d)
    p = DataRepresentation(s)
    p.plot()
