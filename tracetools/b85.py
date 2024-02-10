import numpy as np
import struct

# Decode raw data in Sinumerik XML files
# Uses siemens custom ascii-map for base85


def __encode(data:list[bytes],map:list[chr])->str:

    s = ''
    data = list(data)
    b86_chunks = []

    while len(data) > 0:

        chunk = []
        n_fill = 0
        if len(data)>4:
            chunk = data[0:4]
            data = data[4:]
        else:
            chunk = data
            data = []
            n_fill = 4 - len(chunk)
            fill_bytes = [0 for _ in range(n_fill)]
            chunk.extend(fill_bytes)

        in85 = []
        inT = 0
        for i,chnk in enumerate(chunk):
            inT +=  chnk * 2** ((3 - i)*8)

        #inT = chunk[0]*2**24 + chunk[1]*2**16 + chunk[2]*2**8 + chunk[3]

        for i in range(5):

            tmp = inT % 85
            inT -= tmp

            inT /= 85

            in85.append(int(tmp))

        in85.reverse()
        b86_chunks.append(in85)

        asc85 = [map[c] for c in in85]

        for i,c in enumerate(asc85):
            if i <= (4 - n_fill):
                s += c

    return s,b86_chunks

def _decode(s:str,map:list[chr]=None)->bytearray:

    # This took waaaay to long to find out
    map_def = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$`()*+-/:;=?@[]^_{|}~"

    if map == None:
        map = list(map_def)

    res_bytes = []

    s = str(s)

    while len(s) > 0:

        if len(s) > 5:
            chunk = s[0:5]
            s = s[5:]
        else:
            chunk = s
            s = ''

        b85 = []
        for c in chunk:
            ini = map.index(c)
            b85.append(ini)

        zero_fill = [0 for i in range(5 - len(b85))]
        b85.extend(zero_fill)

        assert len(b85) == 5
        int32 = 0
        for i,b in enumerate(b85):
            int32 += b*85**(4 - i)

        tmp_bytes = int32.to_bytes(4,byteorder='big',signed=False)
        res_bytes.append(tmp_bytes)
    return res_bytes



def str2doubles(s):

    vals = []

    while len(s)>0:

        w0 = bytearray([0,0,0,0])
        w1 = bytearray([0,0,0,0])

        if s[0] != '.':
            s0 = s[0:5]
            s = s[5:]
            w0 = _decode(s0)[0]
        else:
            s = s[1:]

        if s[0] != '.':
            s1 = s[0:5]
            s = s[5:]
            w1 = _decode(s1)[0]
        else:
            s = s[1:]

        w0 = bytearray(w0)
        w1 = bytearray(w1)

        dw = bytearray(w0)
        dw.extend(w1)

        val = struct.unpack('>d',dw)[0]
        vals.append(val)
    return np.array(vals)

