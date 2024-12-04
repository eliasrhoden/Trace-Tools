
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from . import b85
from . import tracetypes as tp
import numpy as np
import pandas as pd


def parse_xml_ts(ts_root):

    num_arr = next(ts_root.iter('raw'))
    data = num_arr.text.replace('\n','').replace(' ','').replace('\t','')
    vals = b85.str2doubles(data)

    tf = -1
    for f in ts_root.iter('float'):
        if f.get('name') == 'm_TimeVector.end':
            tf = float(f.text)
            break

    if tf == -1:
        raise Exception("Failed to find m_TimeVector.end")

    t = np.linspace(0,tf,len(vals))

    return tp.TimeSeries(t,vals)

def parse_xml_freq(fr_root):

    raw_vals = None
    freqs = None

    for na in fr_root.iter('NumericArray'):

        raw = next(na.iter('raw'))

        data = raw.text.replace('\n','').replace('\t','').replace(' ','')
        vals = b85.str2doubles(data)

        name = na.get('name')

        if name == 'm_ValueVector':
            raw_vals = vals
        elif name == 'm_FrequencyVector':
            freqs = vals

    if type(raw_vals) == None and type(freqs) == None:
        raise Exception("Failed to find m_ValueVector and m_FrequencyVector")

    if len(raw_vals) % 2 != 0:
        raise Exception("Must be even nr of doubles in a complex value array")

    complex_vals = []

    i = 0
    while i < len(raw_vals):
        real = raw_vals[i]
        img = raw_vals[i+1]

        complex_vals.append(real + 1j*img)

        i += 2

    assert len(complex_vals) == len(freqs)

    return tp.FreqResponse(freqs,complex_vals)


def plot_freq(f:tp.FreqResponse):

        hz = f.freqs_hz
        mag = f.get_mag()
        phase = f.get_phase()

        f1 = plt.subplot(2,1,1)
        plt.semilogx(hz,mag)
        plt.ylabel('Magnitude [dB]')

        plt.subplot(2,1,2,sharex=f1)
        plt.semilogx(hz,phase)
        plt.ylabel('Phase [Deg]')
        plt.xlabel('Frequency [Hz]')


def find_by_name(root,tag_type,name):

    for item in root.iter(tag_type):
        if item.get('name') == name:
            return item
    raise Exception(f"Could not find <{tag_type} name={name}>")

def find_float_by_name(root,name):

    for c in root:
        if c.get('name') == name:
            return float(c.text)
    raise Exception(f"Could not find <float name={name}>")

def parse_xml_filters(root):
    link_list_of_filters = root.find('LinkedList') 
    filters = []

    for f in link_list_of_filters:

        filter_enabled = 'true' in find_by_name(f,'boolean','m_bFilterIsEnabled').text

        if not filter_enabled:
            continue

        if f.tag == 'PT2Filter':
            freq = find_float_by_name(f,'m_Frequency')
            d = find_float_by_name(f,'m_DampingRatio')
            filters.append(tp.PT2(freq,d))

        elif f.tag == 'PT1Filter':
            tau = find_float_by_name(f,'m_dTimeConst') 
            filters.append(tp.PT1(tau))

        elif f.tag == 'SecondOrderFilter':
            fn = find_float_by_name(f,'m_NumeratorFrequency')
            dn = find_float_by_name(f,'m_NumeratorDampingRatio')
            fd = find_float_by_name(f,'m_DenominatorFrequency')
            dd = find_float_by_name(f,'m_DenominatorDampingRatio')

            filters.append(tp.SecondOrdFilter(fn,dn,fd,dd))

        else:
            raise Exception(f"Unkown filter type! {f.tag}")

    return filters



def parse_xml_speed_ctrl_pars(root,Ts):

    # params
    Kp = find_float_by_name(root,'m_dKpGain')
    Tn = find_float_by_name(root,'m_dIntegralTime')

    using_ref_mdl = 'true' in find_by_name(root,'boolean','m_bUsingReferenceModel').text
    ref_mdl_fr = find_float_by_name(root,'m_dRefmod_freq')
    ref_mdl_d = find_float_by_name(root,'m_dRefmod_damping')
    ref_mdl_timedelay = find_float_by_name(root,'m_dRefmod_tdelay')

    # Current setpoint filters
    filt_list = find_by_name(root,'ConTimeFilterList','m_CurrentFilters')
    current_filters = parse_xml_filters(filt_list)

    # Act value filters
    filt_list = find_by_name(root,'ConTimeFilterList','m_ConTimeFilterListActualSpeedFilters')
    act_value_filters = parse_xml_filters(filt_list)

    return tp.SpeedCtrl(Kp,Tn,Ts, using_ref_mdl, ref_mdl_fr, ref_mdl_d, ref_mdl_timedelay, act_value_filters, current_filters)



def parse_autotune_file(file):

    tree = ET.parse(file)
    root = tree.getroot()


    # Meta data
    ax_name = ''
    machine_name = ''
    timestamp = ''

    for s in root.findall('string'):
        s_name = s.get('name')

        if s_name == 'm_szAxisName':
            ax_name = s.text

        if s_name == 'm_szPlatformName':
            machine_name = s.text

        if s_name == 'm_szInitTime':
            timestamp = s.text


    # Freq meas
    speed_ctrl_root = next(root.iter('DynamicModelPositionController840DSL'))

    Ts = find_by_name(speed_ctrl_root,'float','m_dActValDelayTime')
    Ts = float(Ts.text)

    dynamic_mdl_list = find_by_name(speed_ctrl_root,'DynamicModelList','m_SpeedControllerList')

    plant_freq = None 
    meas_coherence = None 
    current_freq = None

    for fr in dynamic_mdl_list.iter('FrequencyResponseFunction'):
        name = fr.get('name')

        if name == 'm_pPlant':
            plant_freq = parse_xml_freq(fr)

        if name == 'm_pMeasCoherence':
            meas_coherence = parse_xml_freq(fr)

    # current freq response
    for fr in dynamic_mdl_list.iter('FrequencyResponseFunction'):
        name = fr.get('name')

        if name == 'm_pPlant':
            plant_freq = parse_xml_freq(fr)

        if name == 'm_pMeasCoherence':
            meas_coherence = parse_xml_freq(fr)

        if name == 'm_pCurrentFreqResponse':
            current_freq = parse_xml_freq(fr)

    current_freq_xml = find_by_name(speed_ctrl_root,'FrequencyResponseFunction','m_CurrentControllerResponse')
    current_freq = parse_xml_freq(current_freq_xml)


    # Ctrl params
    speed_ctrl_list = find_by_name(speed_ctrl_root,'LinkedList','m_listpSpeedLoopRegulators')

    original_speed_par = None 
    tuned_speed_par = None 

    for i,spd_ctrl in enumerate(speed_ctrl_list):

        if i== 0:
            original_speed_par = parse_xml_speed_ctrl_pars(spd_ctrl,Ts)
        if i == 1:
            tuned_speed_par = parse_xml_speed_ctrl_pars(spd_ctrl,Ts)

    return tp.AutoTuneResult(machine=machine_name,
                                axis_name=ax_name,
                                timestamp=timestamp,
                                speed_ctrl_params=tuned_speed_par,
                                plant_freq_response=plant_freq,
                                freq_meas_coherence=meas_coherence,
                                current_ctrl_freq_response=current_freq)


def parse_freq_meas_file(file):

    tree = ET.parse(file)
    root = tree.getroot()


    # Meta data
    machine_name = ''
    timestamp = ''

    for s in root.findall('string'):
        s_name = s.get('name')

        if s_name == 'm_szPlatformName':
            machine_name = s.text

        if s_name == 'm_szInitTime':
            timestamp = s.text


    # Measured signal
    meas_node = find_by_name(root,'LinkedList','m_MeasurementSignalNodeList')
    ts_signals = []
    for ts_node in meas_node.iter('TimeSeries'):
        ts = parse_xml_ts(ts_node)
        ts_signals.append(ts)

    if len(ts_signals)>=2:
        input_signals = [ts_signals[1]]
        output_signals = [ts_signals[0]]
    else:
        input_signals = []
        output_signals = []

    if len(ts_signals) == 4:
        input_signals = [ts_signals[2],ts_signals[3]]
        output_signals = [ts_signals[0],ts_signals[1]]
        

    cross_spectrums = meas_node.iter('CrossSpectrum')

    input = parse_xml_freq(next(cross_spectrums))
    output = parse_xml_freq(next(cross_spectrums)) #y
    spec_dens = parse_xml_freq(next(cross_spectrums)) #spec eller x

    X = np.array(input.values)
    Y = np.array(output.values)
    W = output.freqs_hz

    G = tp.FreqResponse(W,X/Y)

    return tp.FrequencyMeasurement(
                                    machine=machine_name,
                                    timestamp=timestamp,
                                    input_time_series=input_signals,
                                    output_time_series=output_signals,
                                    input_freq=input,
                                    output_freq=output,
                                    plant_freq_response=G,
                                    cross_spectrum=spec_dens)



def parse_step_response(file):

    tree = ET.parse(file)
    root = tree.getroot()

    TS:list[tp.TimeSeries] = []

    for s in root.iter('TimeSeries'):
        TS.append(parse_xml_ts(s))
    
    TS[0].values = TS[0].values *-1.0
    TS[1].values = TS[1].values *-1.0

    FS = []
    for s in root.iter('CrossSpectrum'):
        FS.append(parse_xml_freq(s))


    return tp.StepResponsefile(input=TS[1],output=TS[0],autospec1=FS[0],crossSpecInfo=FS[1],autospec2=FS[2])
