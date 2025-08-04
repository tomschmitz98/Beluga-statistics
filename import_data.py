import json
import dataclasses
import math


@dataclasses.dataclass(init=True)
class UwbConfigurations:
    id: int = 0
    channel: int = 0
    ds_twr: bool = True
    sfd: bool = False
    amps: str = ""
    data_rate: str = ""
    pulse_rate: str = ""
    phr: bool = False
    preamble: str = ""
    pac: str = ""
    tx_power: str = ""

    def __repr__(self):
        return f"Node ID: {self.id}\n" \
               f"Channel: {self.channel}\n" \
               f"TWR: {'Double sided' if self.ds_twr else 'Single sided'}\n" \
               f"SFD: {'Proprietary' if self.sfd else 'Standard'}\n" \
               f"External Amplifiers: {self.amps}\n" \
               f"Data rate: {self.data_rate}\n" \
               f"Pulse rate: {self.pulse_rate}\n" \
               f"PHR: {'Proprietary' if self.phr else 'Standard'}\n" \
               f"Preamble: {self.preamble}\n" \
               f"PAC: {self.pac}\n" \
               f"{self.tx_power}"


@dataclasses.dataclass(init=True)
class UwbDrops:
    poll_fails: int = 0
    respond_drops: int = 0
    final_fails: int = 0
    report_drops: int = 0
    exchanges: int = 0
    double_sided: bool = False
    poll_events: dict | None = None
    response_events: dict | None = None
    final_events: dict | None = None
    report_events: dict | None = None

    def total_receptions(self):
        successful_receptions = self.exchanges
        if self.double_sided:
            # 2 receptions per exchange
            successful_receptions *= 2
            # Times that respond succeeded, but not report
            successful_receptions += self.report_drops
        return successful_receptions + self.report_drops + self.respond_drops

    def dropped_receptions(self):
        return self.respond_drops + self.report_drops

    def __add__(self, other):
        if self.double_sided == other.double_sided:
            self.poll_fails += other.poll_fails
            self.respond_drops += other.respond_drops
            self.final_fails += other.final_fails
            self.report_drops += other.report_drops
            self.exchanges += other.exchanges


class UwbSamples:
    def __init__(self, samples: list[dict[str, int | float | dict[str, int]]], configs: UwbConfigurations):
        self._rssi: list[int] = []
        self._range: list[float] = []
        self._uwb_diagnostics: list[dict[str, int]] = []
        self._uwb_events: list[dict[str, int]] = []
        self._uwb_rx_power: list[float] = []
        self._uwb_first_path_signal_power: list[float] = []

        for sample in samples:
            self._rssi.append(sample["RSSI"])
            self._range.append(sample["RANGE"])
            self._uwb_diagnostics.append(sample["UWB_DIAGNOSTICS"])
            self._uwb_events.append(sample["EVENTS"])
            diagnostics = sample["UWB_DIAGNOSTICS"]
            self._uwb_rx_power.append(
                self._rx_power(diagnostics["MAX_GROWTH_CIR"], diagnostics["RX_PREAMBLE_CNT"], configs))
            self._uwb_first_path_signal_power.append(
                self._first_path_signal_strength(diagnostics["FIRST_PATH_AMP1"], diagnostics["FIRST_PATH_AMP2"],
                                                 diagnostics["FIRST_PATH_AMP3"], diagnostics["RX_PREAMBLE_CNT"],
                                                 configs))

    @staticmethod
    def _prf_to_a(config):
        if config.pulse_rate == "Pulse Rate: 1 OK":
            return 121.74
        else:
            return 113.77

    def _rx_power(self, c: int, n: int, config: UwbConfigurations) -> float:
        a = self._prf_to_a(config)
        if c == 0:
            c += 1
        log_op = (c * (2 ** 17)) / (n ** 2)
        return (10.0 * math.log10(log_op)) - a

    def _first_path_signal_strength(self, f1: int, f2: int, f3: int, n: int, config: UwbConfigurations) -> float:
        a = self._prf_to_a(config)
        num = (f1 ** 2) + (f2 ** 2) + (f3 ** 2)
        den = n ** 2
        log_op = num / den
        return (10.0 * math.log10(log_op)) - a

    @property
    def rssi(self):
        return self._rssi

    @property
    def range(self):
        return self._range

    @property
    def uwb_rx_power(self):
        return self._uwb_rx_power

    @property
    def uwb_signal_power_in_first_path(self):
        return self._uwb_first_path_signal_power

    @property
    def uwb_diagnostic_info(self):
        return self._uwb_diagnostics

    @property
    def uwb_events(self):
        return self._uwb_events

    def __len__(self):
        return len(self._range)


class UwbData:
    def __init__(self, filepath: str):
        data = None
        with open(filepath, 'r') as f:
            data = json.load(f)

        configs = data["configurations"]
        self._configurations = UwbConfigurations(int(configs["ID"]), int(configs["Channel"]),
                                                 configs["DS-TWR"], configs["SFD"], configs["External Amps"],
                                                 configs["Data rate"], configs["Pulse rate"], configs["PHR"],
                                                 configs["Preamble"], configs["PAC"], configs["TX Power"])

        drops = data["drops"]
        self._drops: dict[str, UwbDrops] = {}
        for id_, item in drops.items():
            self._drops[id_] = UwbDrops(item["0"]["count"], item["1"]["count"], item["2"]["count"], item["3"]["count"],
                                        double_sided=self._configurations.ds_twr, poll_events=item["0"]["events"],
                                        response_events=item["1"]["events"], final_events=item["2"]["events"],
                                        report_events=item["3"]["events"])

        samples = data["samples"]
        self._samples: dict[str, UwbSamples] = {}
        for id_, item in samples.items():
            self._samples[id_] = UwbSamples(item, self._configurations)
            self._drops[id_].exchanges = len(self._samples[id_])

    @property
    def other_nodes(self):
        return list(self._samples.keys())

    @property
    def configurations(self) -> UwbConfigurations:
        return self._configurations

    @property
    def drops(self) -> dict[str, UwbDrops]:
        return self._drops

    @property
    def samples(self) -> dict[str, UwbSamples]:
        return self._samples


if __name__ == "__main__":
    data_ = UwbData("test.json")
    print(data_.other_nodes)
    print(data_.configurations)
