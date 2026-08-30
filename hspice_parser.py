import pandas as pd
import re

""" Example of mt0 file
$DATA1 SOURCE='PrimeSim HSPICE' VERSION='W-2024.09 linux64' PARAM_COUNT=1
.TITLE 'inverter 7x chain -- exercise 1.a, hspice'
 k                tplh             tphl             tr              
                  tf               diff_tplh_tphl   diff_tr_tf      
                  temper           alter#          
    0.5000         4.408e-12        2.578e-12        9.260e-12      
                   4.518e-12        1.829e-12        4.743e-12      
                    25.0000        1               
    0.6029         4.307e-12        2.681e-12        9.013e-12      
                   4.575e-12        1.626e-12        4.438e-12      
                    25.0000        1               
"""
def parse_mto(filepath):
    with open (filepath, 'r') as file:
        lines = file.readlines()
    

    col_headers=[]
    data=[] # completely flate

    # files always start with $DATA1, then .TITLE
    for line in lines[2:]:
        line_str = line.strip()
        if re.match(r'^[0-9]', line_str):
            data.extend(line_str.split()) #split using whitespace
        else: #non number, in header
            col_headers.extend(line_str.split())

    len_data = len(data)
    num_cols = len(col_headers)
    num_rows = int(len_data/num_cols)

    data_idx = 0
    rows = []
    for row_idx in range(num_rows):
        row = data[data_idx:data_idx+num_cols]
        rows.append(row)
        data_idx+=num_cols
    
    df = pd.DataFrame(rows, columns=col_headers, dtype=float) #check if this handles scientific notation
    return df

"""
sw0 example from a .probe on .dc k start={k_start} stop={k_stop} step={k_res}
000200000000000000002001inverter swp 1x loop                                    
        08/30/2026      12:29:32 Copyright (c) 1986 - 2026 by Synopsys, Inc. All
 Rights Reserved.          0                                                    
            3<num value_cols per row>       1<Num indep var>     k               v(in            $&%#    
0.3000000E+000.3638730E+000.4000000E+000.3656395E+000.5000000E+000.3677331E+00
0.6000000E+000.3706443E+000.7000000E+000.3752848E+000.8000000E+000.3801603E+00
"""
def parse_sw0(filepath):
    with open (filepath, 'r') as file:
        raw_data = file.read()

    col_headers = []
    in_header = False
    for item in raw_data.split():
        if item == "Reserved.":
            in_header = True
            continue
        if in_header:
            if item == "$&%#":
                break
            else:
                col_headers.append(item)
    col_headers.pop(0) #number following reserved
    col_headers.pop(0) #arg for num of value columsn per row
    col_headers.pop(0) #arg for num of indep vars swept


    float_pattern = re.compile(r'[+-]?\d+\.\d+[eE][-+]\d{2}')
    data = [float(val) for val in float_pattern.findall(raw_data)]

    #data is currently all flat
    # doing the same reshaping as I did in prev function but doing it all at once
    num_cols = len(col_headers)
    rows = (data[data_idx:data_idx+num_cols] for data_idx in range(0, len(data), num_cols))

    df = pd.DataFrame(rows, columns=col_headers, dtype=float) #check if this handles scientific notation
    return df