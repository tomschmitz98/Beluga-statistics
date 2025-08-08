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
        self._stats.stats.set_index('range', inplace=True)
        y = [self._stats.stats.loc[distance, 'rssi_mean'] - base for distance in x]

        fig, ax = plt.subplots()
        bars = ax.bar(x_labels, y, align='center', width=1.0, bottom=base)

        for bar in bars:
            yval = bar.get_height() + base
            ax.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, f"{yval}", ha='center', va='bottom', rotation=45)

        ax.set_yticks(range(base, 0, 10))

        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("RSSI (dBm)")
        ax.set_title("Average RSSI at Distances")

        if self._save_dir is not None:
            fname = self._save_dir / "distance_v_rssi.png"
            fig.savefig(fname)

    def plot(self):
        if self._enable.rssi:
            self._plot_avg_rssi()

        if self._show:
            plt.show()


if __name__ == "__main__":
    d = {
        10: UwbData("data/Node 100/10m.json"),
        20: UwbData("data/Node 100/20m.json")
    }
    s = UwbStats(d)
    p = DataRepresentation(s)
    p.plot()
