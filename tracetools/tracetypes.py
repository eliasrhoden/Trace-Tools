import dataclasses
import numpy as np


@dataclasses.dataclass
class PT2:
    freq:float
    damping:float

@dataclasses.dataclass
class PT1:
    time_const:float

@dataclasses.dataclass
class SecondOrdFilter:
    num_f:float
    num_d:float
    den_f:float
    den_d:float

@dataclasses.dataclass
class SpeedCtrl:
    Kp:float
    Ti:float
    
    Ts:float

    ref_mdl_active:bool
    ref_mdl_freq:float
    ref_mdl_d:float
    ref_mdl_delay:float

    act_value_filters:list
    current_setp_filters:list

@dataclasses.dataclass
class FreqResponse:
    freqs_hz:np.ndarray
    values:np.ndarray

    def get_mag(self):
        return np.log10(np.abs(self.values))*20

    def get_phase(self):
        return np.rad2deg(np.angle(self.values))


@dataclasses.dataclass
class TimeSeries:
    t:np.ndarray
    values:np.ndarray


@dataclasses.dataclass
class Trace:
    name:str
    nck_path:str
    time:np.array
    signal:np.array


@dataclasses.dataclass
class AutoTuneResult:
    machine:str
    axis_name:str
    timestamp:str

    speed_ctrl_params:SpeedCtrl

    plant_freq_response:FreqResponse
    freq_meas_coherence:FreqResponse
    current_ctrl_freq_response:FreqResponse

@dataclasses.dataclass
class StepResponsefile:
    input:TimeSeries
    output:TimeSeries

    autospec1:FreqResponse
    autospec2:FreqResponse
    crossSpecInfo: FreqResponse





@dataclasses.dataclass
class FrequencyMeasurement:
    machine:str
    timestamp:str

    # When doing frequency measurements, you often do one in positive dir
    # and then one in the reverse dir, thus there are two pairs of timeseries, but only one freq response
    input_time_series:list[TimeSeries]
    output_time_series:list[TimeSeries]

    input_freq:FreqResponse
    output_freq:FreqResponse
    plant_freq_response:FreqResponse
    cross_spectrum:FreqResponse

