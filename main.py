import json
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

        def individual_run(folder: Path) -> UwbStats:
            data: dict[int, UwbData] = {}
            for f in folder.glob("*.json"):
                distance = self._extract_distance(f.name, f.absolute())
                data[distance] = UwbData(str(f))
            return UwbStats(data)

        def multiple_folders() -> dict[str, UwbStats]:
            data: dict[str, UwbStats] = {}
            for folder in self._folder.iterdir():
                if folder.is_dir():
                    data[str(folder.name)] = individual_run(folder)
            return data

        if list(self._folder.glob("*.json")):
            self._stats: UwbStats | dict[str, UwbStats] = individual_run(self._folder)
            self._graphs = DataRepresentation(self._stats, show, enable, save_dir)
            self._dirs = None
        else:
            self._stats: UwbStats | dict[str, UwbStats] = multiple_folders()
            self._dirs = list(self._stats.keys())
            if save_dir is None:
                self._graphs = {key: DataRepresentation(value, show, enable, save_dir) for key, value in self._stats.items()}
            else:
                self._graphs = {}
                for key, value in self._stats.items():
                    _save_dir = save_dir / key
                    _save_dir.mkdir(exist_ok=True)
                    self._graphs[key] = DataRepresentation(value, show, enable, _save_dir)


    @staticmethod
    def _extract_distance(name, absolute_path) -> int:
        def extract_from_file():
            with open(absolute_path) as f:
                data = json.load(f)
            return data['distance']

        def extract_from_file_name():
            regex = re.compile(f'\d+')
            numbers = [int(x) for x in regex.findall(name)]
            if not numbers:
                raise ValueError("Improperly named file")
            return numbers[0]

        try:
            return extract_from_file()
        except KeyError:
            return extract_from_file_name()

    def log_ranging(self, callback: Callable[[any], None] = print, run: str | None = None):
        if isinstance(self._stats, UwbStats):
            self._stats.log_range(callback)
        elif run is not None:
            self._stats[run].log_range(callback)
        else:
            raise ValueError("`run` must not be `None`")

    def log_rssi(self, callback: Callable[[any], None] = print, run: str | None = None):
        if isinstance(self._stats, UwbStats):
            self._stats.log_rssi(callback)
        elif run is not None:
            self._stats[run].log_rssi(callback)
        else:
            raise ValueError("`run` must not be `None`")

    def log_rx_power(self, callback: Callable[[any], None] = print, run: str | None = None):
        if isinstance(self._stats, UwbStats):
            self._stats.log_uwb_power(callback)
        elif run is not None:
            self._stats[run].log_uwb_power(callback)
        else:
            raise ValueError("`run` must not be `None`")

    def log_uwb_stats(self, callback: Callable[[any], None] = print, run: str | None = None):
        if isinstance(self._stats, UwbStats):
            self._stats.log_uwb_prr(callback)
        elif run is not None:
            self._stats[run].log_uwb_prr(callback)
        else:
            raise ValueError("`run` must not be `None`")

    def plot(self):
        if isinstance(self._graphs, DataRepresentation):
            self._graphs.plot()
        else:
            for graph in self._graphs.values():
                graph.plot()

    @property
    def dir_names(self) -> list[str] | None:
        return self._dirs


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

    Path("./results").mkdir(exist_ok=True)

    for node in nodes:
        dir_ = create_dir(node)
        data = BelugaDataProcessing(node, show_plots, enable, dir_)

        if data.dir_names is None:
            with open(dir_ / "rssi.log", "w") as rssi_log:
                data.log_rssi(rssi_log.write)
            with open(dir_ / "ranging.log", "w") as ranging_log:
                data.log_ranging(ranging_log.write)
            with open(dir_ / "rx_power.log", "w") as power_log:
                data.log_rx_power(power_log.write)
            with open(dir_ / "uwb_stats.log", "w") as stats_log:
                data.log_uwb_stats(stats_log.write)
        else:
            for run in data.dir_names:
                save_dir = dir_ / run
                with open(save_dir / "rssi.log", "w") as rssi_log:
                    data.log_rssi(rssi_log.write, run)
                with open(save_dir / "ranging.log", "w") as ranging_log:
                    data.log_ranging(ranging_log.write, run)
                with open(save_dir / "rx_power.log", "w") as power_log:
                    data.log_rx_power(power_log.write, run)
                with open(save_dir / "uwb_stats.log", "w") as stats_log:
                    data.log_uwb_stats(stats_log.write, run)
        data.plot()

if __name__ == "__main__":
    main(SHOW_PLOTS, ENABLE)
