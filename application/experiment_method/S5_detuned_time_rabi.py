# Import necessary file
from pathlib import Path
link_path = Path(__file__).resolve().parent.parent/"config_api"/"config_link.toml"

from QM_driver_AS.ultitly.config_io import import_config, import_link
link_config = import_link(link_path)
config_obj, spec = import_config( link_path )

config = config_obj.get_config()
qmm, _ = spec.buildup_qmm()

from ab.QM_config_dynamic import initializer

from exp.save_data import save_nc, save_fig

import matplotlib.pyplot as plt

# Set parameters





from exp.config_par import *
from exp.rabi import RabiTime

my_exp = RabiTime(config, qmm)
my_exp.initializer = initializer(200000,mode='wait')

my_exp.ro_elements = [ "q1_ro"]
my_exp.xy_elements = ['q1_xy']

my_exp.freq_range = (-20,20)
my_exp.freq_resolution = 2

my_exp.time_range = (16,200) # ns
my_exp.time_resolution = 8

my_exp.process = "time"

dataset = my_exp.run(200)

save_data = True
save_dir = link_config["path"]["output_root"]
save_name = f"{my_exp.xy_elements[0]}_{my_exp.process}_Rabi"

if save_data: save_nc(save_dir, save_name, dataset)

y = dataset.coords["time"].values
freqs = dataset.coords["frequency"].values
# Plot 
from exp.old_version.rabi import plot_ana_freq_time_rabi 
for ro_name, data in dataset.data_vars.items():
    xy_LO = dataset.attrs["ref_xy_LO"][0]/1e6
    xy_IF_idle = dataset.attrs["ref_xy_IF"][0]/1e6
    fig, ax = plt.subplots(2)
    plot_ana_freq_time_rabi( data, freqs, y, xy_LO, xy_IF_idle, ax )
    ax[0].set_title(ro_name)
    ax[1].set_title(ro_name)

if save_data: save_fig(save_dir, save_name)

plt.show()