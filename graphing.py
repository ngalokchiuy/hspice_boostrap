# to make sure wsl does not try to open a gui
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from scipy.stats import linregress
import numpy as np
import seaborn as sns

# Expanded grayscale specs for main traces (high value contrast, varying styles/markers)
style_specs = [
    {'color': '#000000', 'linestyle': '-',  'marker': 'o', 'linewidth': 2.2}, # Black, solid, circle
    {'color': '#333333', 'linestyle': '--', 'marker': 's', 'linewidth': 2.0}, # Dark gray, dashed, square
    {'color': '#666666', 'linestyle': '-.', 'marker': '^', 'linewidth': 2.0}, # Mid gray, dash-dot, triangle up
    {'color': '#999999', 'linestyle': ':',  'marker': 'D', 'linewidth': 2.5}, # Light gray, dotted, diamond
    {'color': '#000000', 'linestyle': '--', 'marker': 'v', 'linewidth': 2.0}, # Black, dashed, triangle down
    {'color': '#444444', 'linestyle': '-',  'marker': 'p', 'linewidth': 2.2}, # Dark gray, solid, pentagon
    {'color': '#777777', 'linestyle': ':',  'marker': '*', 'linewidth': 2.5}, # Mid gray, dotted, star
    {'color': '#111111', 'linestyle': '-.', 'marker': 'h', 'linewidth': 2.0}, # Charcoal, dash-dot, hexagon
]

# Color-blind friendly Okabe-Ito palette for extra traces (thinner lines, distinct shapes)
extra_style_specs = [
    {'color': '#D55E00', 'linestyle': '--', 'marker': 'X', 'linewidth': 1.2}, # Vermillion (Red-ish)
    {'color': '#0072B2', 'linestyle': '--', 'marker': 'P', 'linewidth': 1.2}, # Blue
    {'color': '#009E73', 'linestyle': '--', 'marker': 'd', 'linewidth': 1.2}, # Bluish Green (fallback)
]

def plot_series(x_data, y_dict, extra_x_dict=None, extra_y_dict=None, xlabel="Time (ps)", ylabel="Voltage (V)", title="Simulation", filename="graphs/plot.png"):
    """
    y_dict: {"signal": np_array}
    extra_x_dict: {"trace_name": np_array} - Explicit X mapping for extra traces
    extra_y_dict: {"trace_name": np_array} - Explicit Y mapping for extra traces
    """
    # Plot standard y_dict traces using the single x_data array
    for idx, (label, y_data) in enumerate(y_dict.items()):
        spec = style_specs[idx % len(style_specs)] 
        
        plt.plot(
            x_data, y_data,
            label=label,
            color=spec['color'],
            linestyle=spec['linestyle'],
            marker=spec['marker'],
            linewidth=spec['linewidth'],
            markevery=max(1, len(x_data) // 15), 
            markersize=6
        )
        
    # Plot the extra 1-to-1 mapped traces using the new extra_style_specs
    if extra_x_dict and extra_y_dict:
        extra_idx = 0
        for label in extra_x_dict.keys():
            if label in extra_y_dict:
                x_arr = extra_x_dict[label]
                y_arr = extra_y_dict[label]
                
                # Grab the style for the extra trace
                spec = extra_style_specs[extra_idx % len(extra_style_specs)]
                
                plt.plot(
                    x_arr, y_arr, 
                    label=label, 
                    color=spec['color'], 
                    linestyle=spec['linestyle'], 
                    marker=spec['marker'], 
                    linewidth=spec['linewidth'], 
                    markersize=8, 
                    zorder=5
                )
                extra_idx += 1
        
    plt.xlabel(xlabel, fontweight='bold')
    plt.ylabel(ylabel, fontweight='bold')
    plt.title(title, fontweight='bold')
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(frameon=True, edgecolor='black')
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.show()

def find_lin_to_sat_point(vds, ids, r_threshold=0.995):
    """
    Finds the (Vds, Ids) point where the MOSFET transitions from linear to saturation.
    Uses abs(r_value) to support both NMOS (positive) and PMOS (negative) curves.
    """
    for i in range(3, len(vds) + 1):
        slope, intercept, r_value, p_value, std_err = linregress(vds[:i], ids[:i])
        
        # Take the absolute value so negative PMOS slopes (-1.0) don't immediately trigger
        if abs(r_value) < r_threshold:
            vds_sat = vds[i-1]
            ids_sat = ids[i-1]
            print(f"Transition found: Vds = {vds_sat}V, Ids = {ids_sat:.2e}A")
            return vds_sat, ids_sat
            
    print("Warning: Curve never significantly deviated from linearity.")
    return vds[-1], ids[-1]


def generate_leakage_heatmap(data_dict, filename:str):
    """
    Takes a dictionary containing lists of floats, converts to absolute nA, 
    and generates a heatmap.
    """
    circuits = ["circuit A", "circuit B", "circuit C", "circuit D"]
    inputs = ["00", "01", "10", "11"]
    
    # 1. Parse the dictionary and process the data
    processed_data = []
    for key in circuits:
        # Get the list of floats directly from the dictionary
        raw_list = data_dict[key] 
        
        # Take the absolute value and scale to nA (1e9) for each item in the list
        row_data = [abs(val) * 1e9 for val in raw_list]
        processed_data.append(row_data)
        
    # Convert to a NumPy array and transpose (.T) so inputs are rows and circuits are columns
    data_array = np.array(processed_data).T
    
    # 2. Configure and draw the heatmap
    plt.figure(figsize=(9, 6))
    
    # Using 'YlOrRd' (Yellow-Orange-Red) colormap to highlight higher leakage
    ax = sns.heatmap(data_array, annot=True, fmt=".3f", cmap="YlOrRd",
                     xticklabels=circuits, yticklabels=inputs,
                     cbar_kws={'label': 'Leakage Current (nA)'})
    
    # 3. Format titles and labels
    plt.title("Static Leakage Current in Sleep Mode (S=1)", fontsize=14, pad=15)
    plt.xlabel("Circuit Configuration", fontsize=12, labelpad=10)
    plt.ylabel("Input State (ab)", fontsize=12, labelpad=10)
    
    # Rotate the y-axis labels so they are upright
    plt.yticks(rotation=0)
    
    # Optimize layout and display
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.show()