import numpy as np
import matplotlib.pyplot as plt
import xarray as xr

# Load the dataset
filename = r"C:\Users\quant\SynologyDrive\09 Data\Fridge Data\Qubit\20240920_DRKe_5Q4C\save_data\CZ_sweet\crosstalk_not_compensated\phase_check\phase_ramsey\20241004_122121_CZ_diff\q1q0_cz_phasediff_shot.nc"
dataset = xr.open_dataset(filename, engine='netcdf4', format='NETCDF4')

# Print the dataset structure
print(dataset)

# Extract the "I" component for "q0_ro"
data_q0_I = dataset["q0_ro"].sel(mixer="I")

# Taking the average and standard deviation across "shot"
data_q0_I_avg = data_q0_I.mean(dim="shot")
data_q0_I_std = data_q0_I.std(dim="shot")

# Selecting the first elements of "c_amp" and "cz_amp", and setting "rotate" to 0
data_q0_I_avg_filtered = data_q0_I_avg.sel(c_amp=dataset.coords['c_amp'][0], cz_amp=dataset.coords['cz_amp'][0])
data_q0_I_std_filtered = data_q0_I_std.sel(c_amp=dataset.coords['c_amp'][0], cz_amp=dataset.coords['cz_amp'][0])

# Now plot for both `control=0` and `control=1` on the same plot with error bars
phase = dataset.coords['phase']
plt.figure()

# Control = 0 with error bars (sigma)
plt.errorbar(phase, data_q0_I_avg_filtered.sel(control=0),
             #yerr=data_q0_I_std_filtered.sel(control=0),
             label='Control = 0', fmt='-o', capsize=3)

# Control = 1 with error bars (sigma)
plt.errorbar(phase, data_q0_I_avg_filtered.sel(control=1),
             #yerr=data_q0_I_std_filtered.sel(control=1),
             label='Control = 1', fmt='-o', capsize=3)

# Add vertical lines at phase = 0.65 and phase = 0.15
plt.axvline(x=0.65, color='red', linestyle='--', label='Phase = 0.65')
plt.axvline(x=0.15, color='green', linestyle='--', label='Phase = 0.15')

# Add labels and title
plt.xlabel('Phase')
plt.ylabel('I Component')
plt.title('q0_ro I component over Phase for Control = 0 and 1')
plt.legend()
plt.grid(True)
plt.show()

# Function to plot IQ plane for a specific phase
def plot_IQ_plane(dataset, phase_value):
    # Extract the shots for the specified phase
    shots_control_0 = dataset["q0_ro"].sel(control=0, phase=phase_value, method='nearest')
    shots_control_1 = dataset["q0_ro"].sel(control=1, phase=phase_value, method='nearest')

    # Get the I and Q components
    I_control_0 = shots_control_0.sel(mixer="I")
    Q_control_0 = shots_control_0.sel(mixer="Q")

    I_control_1 = shots_control_1.sel(mixer="I")
    Q_control_1 = shots_control_1.sel(mixer="Q")

    # Plot the IQ plane
    plt.figure(figsize=(8, 8))
    plt.scatter(I_control_0, Q_control_0, color='blue', label='Control = 0', alpha=0.5)
    plt.scatter(I_control_1, Q_control_1, color='orange', label='Control = 1', alpha=0.5)

    # Add labels and title
    plt.xlabel('I Component')
    plt.ylabel('Q Component')
    plt.title(f'IQ Plane at Phase = {phase_value}')
    plt.axhline(0, color='black', lw=0.5, ls='--')
    plt.axvline(0, color='black', lw=0.5, ls='--')
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    plt.show()

# Input the phase value you want to visualize
input_phase = 0.15  # 這裡替換成你想要的相位值
plot_IQ_plane(dataset, input_phase)
