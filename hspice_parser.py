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
