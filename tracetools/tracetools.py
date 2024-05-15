import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from . import tracetypes as tp
import numpy as np
import pandas as pd

def parse_trace_file(filename)->list[tp.Trace]:

    root = ET.parse(filename).getroot()
    signal_meta_data = _find_signal_names(root)

    trace = root.find('traceData')
    df = trace.find('dataFrame')

    signals = []
    time_vecs = []

    signals = [[] for i in signal_meta_data]
    time_vecs = [[] for i in signal_meta_data]

    for c in df.iter('rec'):
        time = float(c.attrib['time'])
        for att in c.attrib.keys():
            if att[0] == 'f':
                indx = int(att.replace('f','')) - 1
                sig_val = float(c.attrib[att])
                signals[indx].append(sig_val)
                time_vecs[indx].append(time) 

    traces = []

    for i,data in enumerate(signal_meta_data):
        name = data[0]
        descr = data[1]
        trace = tp.Trace(name,descr,np.array(time_vecs[i]),np.array(signals[i]))
        traces.append(trace)
    return traces

def _find_signal_names(root):
    dispSetup = root.find('traceDisplaySetup')
    
    signals = []

    for s in dispSetup.find("signals"):
        desc = s.attrib['description']
        name = s.attrib['name']
        signals.append((desc,name))

    return signals

def plot_trace(T:tp.Trace,c=''):
    plt.plot(T.time,T.signal,c)
    plt.xlabel('Time [s]')
    plt.title(T.nck_path)

def save_signals_as_csv(signals:list[tp.Trace],filename):
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

