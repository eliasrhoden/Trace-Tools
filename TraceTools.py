
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import b85
import tracetypes as tp
import numpy as np
import pandas as pd




def parse_trace_file(filename)->list[Trace]:
    root = ET.parse(filename).getroot()

    trace = root.find('traceData')

    df = trace.find('dataFrame')

    signal_names = []
    signal_paths = []
    signals = []
    time_vecs = []

    for c in df:
        tag = c.tag 
        if tag == 'dataSignal':
            signal_names.append(c.attrib['description'])
            signal_paths.append(c.attrib['name'])
        if tag == 'rec':
            break

    signal_names = [name.replace('(64 bit)','') for name in signal_names]

    signals = [[] for i in signal_names]
    time_vecs = [[] for i in signal_names]

    for c in df:
        tag = c.tag 
        if tag == 'rec':
            time = float(c.attrib['time'])
            for att in c.attrib.keys():
                if att[0] == 'f':
                    indx = int(att.replace('f','')) - 1
                    sig_val = float(c.attrib[att])
                    if sig_val > 9218868437227405000:
                        if len(signals[indx]) == 0:
                            sig_val = 0
                        else:
                            sig_val = signals[indx][-1]
                    signals[indx].append(sig_val)
                    time_vecs[indx].append(time)


    # remove first sample
    signals = [s[1:] for s in signals]
    time_vecs = [t[1:] for t in time_vecs]

    traces = []

    for i,name in enumerate(signal_names):
        trace = Trace(name,signal_paths[i],np.array(time_vecs[i]),np.array(signals[i]))
        traces.append(trace)
    return traces

def plot_trace(T:Trace,c=''):
    plt.plot(T.time,T.signal,c)
    plt.xlabel('Time [s]')
    plt.title(T.nck_path)

def save_signals_as_csv(signals:list[Trace],filename):
    data = []
    columns = []

    for i,s in enumerate(signals):
        signal_name = s.nck_path.split('/')[-1]
        data.append(s.time)
        data.append(s.signal)
        columns.append(f"time_{signal_name}")
        columns.append(signal_name)
            
    
    df = pd.DataFrame(data,columns)

    df.to_csv(filename.replace('.xml','.csv'))



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

    return t,vals

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



def parse_freq_meas(file):

    tree = ET.parse(file)
    root = tree.getroot()

    TS = []

    for ts in root.iter('TimeSeries'):
        print(ts)
        ts = parse_xml_ts(ts)
        TS.append(ts)
        plt.figure()
        plt.plot(ts[0],ts[1])

    FS = []

    for cs in root.iter('CrossSpectrum'):

        if len(FS) >= 2:
            break

        print(cs)
        fs = parse_xml_freq(cs)
        FS.append(fs)

        mag = np.abs(fs[1])
        mag = 20*np.log10(mag)
        ph = np.angle(fs[1])
        ph = np.rad2deg(ph)

        plt.figure()
        plt.subplot(2,1,1)
        plt.semilogx(fs[0],mag)

        plt.subplot(2,1,2)
        plt.semilogx(fs[0],ph)


    plt.show()


def plot_freq(f:tp.FreqResponse):

        hz = f.freqs_hz
        mag = f.get_mag()
        phase = f.get_phase()

        f1 = plt.subplot(2,1,1)
        plt.semilogx(hz,mag)

        plt.subplot(2,1,2,sharex=f1)
        plt.semilogx(hz,phase)


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
    Tn = find_float_by_name(root,'m_dIntegralTime')*1/1000

    using_ref_mdl = bool(find_by_name(root,'boolean','m_bUsingReferenceModel'))
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

    for fr in dynamic_mdl_list.iter('FrequencyResponseFunction'):
        name = fr.get('name')

        if name == 'm_pPlant':
            plant_freq = parse_xml_freq(fr)

        if name == 'm_pMeasCoherence':
            meas_coherence = parse_xml_freq(fr)


    # Ctrl params
    speed_ctrl_list = find_by_name(speed_ctrl_root,'LinkedList','m_listpSpeedLoopRegulators')

    original_speed_par = None 
    tuned_speed_par = None 

    for i,spd_ctrl in enumerate(speed_ctrl_list):

        if i== 0:
            original_speed_par = parse_xml_speed_ctrl_pars(spd_ctrl,Ts)
        if i == 2:
            tuned_speed_par = parse_xml_speed_ctrl_pars(spd_ctrl,Ts)

    return tp.AutoTuneResult(machine=machine_name,
                                axis_name=ax_name,
                                timestamp=timestamp,
                                speed_ctrl_params=tuned_speed_par,
                                plant_freq_response=plant_freq,
                                freq_meas_coherence=meas_coherence)


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

    input_signals = [ts_signals[1]]
    output_signals = [ts_signals[0]]

    if len(ts_signals) == 4:
        input_signals = [ts_signals[2],ts_signals[3]]
        output_signals = [ts_signals[0],ts_signals[1]]
        

    cross_spectrums = meas_node.iter('CrossSpectrum')

    spec_dens = parse_xml_freq(next(cross_spectrums))
    freq_resp = parse_xml_freq(next(cross_spectrums))

    return tp.FrequencyMeasurement(
                                    machine=machine_name,
                                    timestamp=timestamp,
                                    input_time_series=input_signals,
                                    output_time_series=output_signals,
                                    plant_freq_response=freq_resp,
                                    cross_spectrum=spec_dens)

if __name__ ==  '__main__':
    #a = par('xml files\\tuning_export.xml')
    freq_meas = parse_freq_meas_file(r'xml files\freq_trace.XML')

    plot_freq(freq_meas.plant_freq_response)

    plt.show()