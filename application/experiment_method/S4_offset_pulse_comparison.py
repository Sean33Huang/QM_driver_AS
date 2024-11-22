# Import necessary libraries
from pathlib import Path
from QM_driver_AS.ultitly.config_io import import_config, import_link
from ab.QM_config_dynamic import initializer
from exp.flux_length_check import Flux_length_check
from qualang_tools.plot import Fit
from exp.save_data import DataPackager
from exp.plotting import PainterFluxCheck
import numpy as np


import matplotlib.pyplot as plt

# Load the link and configuration
link_path = Path(__file__).resolve().parent.parent/"config_api"/"config_link.toml"
link_config = import_link(link_path)
config_obj, spec = import_config(link_path)

config = config_obj.get_config()
qmm, _ = spec.buildup_qmm()

# Initialize experiment parameters
my_exp = Flux_length_check(config, qmm)
my_exp.ro_elements = ["q4_ro"]
my_exp.xy_elements = ['q4_xy']
my_exp.z_elements = ['q4_z']
my_exp.initializer = initializer(100000, mode='wait')

# Parameters for pulse-type experiments
my_exp.flux_type = "pulse"  # Set flux_type to "pulse"
my_exp.xy_amp_mod = 0.01
my_exp.flux_quanta = 0.66
my_exp.set_flux_quanta = 0.1
my_exp.freq_range = (-100, 0)
my_exp.freq_resolution = 0.1

# Set multiple driving times for the experiment
xy_driving_times = [10, 100, 1000]  # Add more values as needed
frequencies = []  # List to store extracted frequencies

# Save directory setup
folder_label = "Flux_length_check"
save_dir = link_config["path"]["output_root"]
dp = DataPackager(save_dir, folder_label)

# Initialize painter for plotting
painter = PainterFluxCheck()

# Loop through each xy_driving_time and run the experiment
for xy_time in xy_driving_times:
    my_exp.xy_driving_time = xy_time
    dataset = my_exp.run(100)  # Run the experiment
    fit = Fit()
    res = fit.transmission_resonator_spectroscopy( dataset.coords["frequency"].values*1e6, dataset[my_exp.ro_elements[0]].values[0], plot=False)
    frequency = res["f"][0] * 1e-6 + dataset.attrs["xy_LO"][0]/1e6 + dataset.attrs["xy_IF"][0]/1e6
    frequencies.append(frequency)  # Store the frequency
    
    # Save the data
    dp.save_config(config)
    dp.save_nc(dataset, f"pulse_{xy_time}")
    
    # Plot the dataset for the current xy_time
    fig_name = f"pulse_{xy_time}"
    figs = painter.plot(dataset, fig_name, show=False)
    dp.save_figs(figs)

# Now, run a single "offset" flux type experiment using the middle xy_driving_time
middle_xy_driving_time = xy_driving_times[len(xy_driving_times) // 2]  # Get the middle xy_driving_time
my_exp.flux_type = "offset"  # Change to "offset"
my_exp.xy_driving_time = middle_xy_driving_time  # Set to the middle value
offset_dataset = my_exp.run(100)  # Run offset experiment
fit = Fit()
res = fit.transmission_resonator_spectroscopy( offset_dataset.coords["frequency"].values*1e6, offset_dataset[my_exp.ro_elements[0]].values[0], plot=False)
offset_frequency = res["f"][0] * 1e-6 + offset_dataset.attrs["xy_LO"][0]/1e6 + offset_dataset.attrs["xy_IF"][0]/1e6

# Save offset data and plot
dp.save_nc(offset_dataset, f"offset")
fig_name = f"offset"
offset_figs = painter.plot(offset_dataset, fig_name, show=False)
dp.save_figs(offset_figs)

# Plotting frequencies vs xy_driving_time
fig = plt.figure(figsize=(8, 6))  # Assign the figure to 'fig'
plt.plot(np.log10(xy_driving_times), frequencies, label='Pulse', marker='o', linestyle='-')
plt.axhline(offset_frequency, color='r', linestyle='--', label=f'Offset')  # Add horizontal line for offset frequency
plt.xlabel('Z Time[log(us)]')
plt.ylabel('Frequency[MHz]')
plt.title('Frequency vs Z Time')
plt.legend()
plt.grid(True)

# Save and show the final plot
dp.save_fig(fig, "comparison")
plt.show()

