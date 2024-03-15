import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from . import tracetypes as tp
import numpy as np
import pandas as pd


def parse_trace_file(filename)->list[tp.Trace]:
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
        trace = tp.Trace(name,signal_paths[i],np.array(time_vecs[i]),np.array(signals[i]))
        traces.append(trace)
    return traces

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

