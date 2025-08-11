from collections.abc import Callable

from import_data import UwbData
from process_data import UwbStats
from data_representation import GraphEnable, DataRepresentation
from pathlib import Path
import re


SHOW_PLOTS = False
ENABLE = GraphEnable(
    cir=True,
    ranging_err=True,
    distance=True,
    prr=True,
    rssi=True,
    rx_pow=True,
    fp_pow=True,
    rx_fp_diff=True
)


class BelugaDataProcessing:
    def __init__(self, node: int, show: bool = False, enable: GraphEnable = GraphEnable(), save_dir: Path | None = None):
        self._folder: Path = Path(f"data/Node {node}")
        data: dict[int, UwbData] = {}
        for f in self._folder.glob("*.json"):
            distance = self._extract_distance(f.name)
            data[distance] = UwbData(str(f))
        self._stats = UwbStats(data)
        self._graphs = DataRepresentation(self._stats, show, enable, save_dir)

    @staticmethod
    def _extract_distance(name) -> int:
        regex = re.compile(f'\d+')
        numbers = [int(x) for x in regex.findall(name)]
        if not numbers:
            raise ValueError("Improperly named file")
        return numbers[0]

    def log_ranging(self, callback: Callable[[any], None] = print):
        self._stats.log_range(callback)

    def log_rssi(self, callback: Callable[[any], None] = print):
        self._stats.log_rssi(callback)

    def log_rx_power(self, callback: Callable[[any], None]):
        self._stats.log_uwb_power(callback)

    def log_uwb_stats(self, callback: Callable[[any], None]):
        self._stats.log_uwb_prr(callback)

    def plot(self):
        self._graphs.plot()


def collect_data_naming() -> list[int]:
    data_dir = Path("./data")
    ret: list[int] = [int(str(x.stem).split()[-1]) for x in data_dir.iterdir()]
    return ret

def create_dir(node: int) -> Path:
    dir_name = f"Node {node}"
    dir_ = Path(f"./results/{dir_name}")
    dir_.mkdir(exist_ok=True)
    return dir_

def main(show_plots: bool = False, enable: GraphEnable = GraphEnable()):
    nodes = collect_data_naming()

    for node in nodes:
        dir_ = create_dir(node)
        data = BelugaDataProcessing(node, show_plots, enable, dir_)
        with open(dir_ / "rssi.log", "w") as rssi_log:
            data.log_rssi(rssi_log.write)
        with open(dir_ / "ranging.log", "w") as ranging_log:
            data.log_ranging(ranging_log.write)
        with open(dir_ / "rx_power.log", "w") as power_log:
            data.log_rx_power(power_log.write)
        with open(dir_ / "uwb_stats.log", "w") as stats_log:
            data.log_uwb_stats(stats_log.write)
        data.plot()

if __name__ == "__main__":
    main(SHOW_PLOTS, ENABLE)
