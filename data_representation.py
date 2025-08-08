import matplotlib.pyplot as plt
import dataclasses
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
    def __init__(self, stats: UwbStats, show: bool = True, enable: GraphEnable = GraphEnable()):
        self._stats = stats
        self._enable = enable
        self._show = show

    def _plot_avg_rssi(self):
        base = -100
        x = self._stats.distances
        x.sort()
        x_labels = [str(i) for i in x]
        self._stats.stats.set_index('range', inplace=True)
        y = [self._stats.stats.loc[distance, 'mean_rssi'] for distance in x]

        fig, ax = plt.subplots()
        bars = ax.bar(x_labels, y, align='center', width=1.0)

    def plot(self):
        if self._enable.rssi:
            self._plot_avg_rssi()

        if self._show:
            plt.show()
