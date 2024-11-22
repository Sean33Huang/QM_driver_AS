# Import necessary file
from pathlib import Path
link_path = Path(__file__).resolve().parent.parent/"config_api"/"config_link.toml"

from QM_driver_AS.ultitly.config_io import import_config, import_link
link_config = import_link(link_path)
config_obj, spec = import_config( link_path )

config = config_obj.get_config()
qmm, _ = spec.buildup_qmm()

from ab.QM_config_dynamic import initializer

import matplotlib.pyplot as plt

from visualization.find_ZZfree_plot import plot_pureZZ

import xarray as xr

# Set parameters
from exp.T2_spectrum import T2_Echo_spectrum, T2_Ramsey_spectrum
my_exp = T2_Echo_spectrum(config, qmm)
#now only plot the first ro_element
my_exp.ro_elements = ["q4_ro", "q3_ro"]
my_exp.xy_elements = ["q4_xy"]
my_exp.z_elements = ["q4_z"]
my_exp.time_range = (4, 20000) #ns
my_exp.time_resolution = 200
my_exp.flux_range = ( -0.3, 0.3 )
my_exp.resolution = 0.006


my_exp.initializer = initializer(100000,mode='wait')
dataset = my_exp.run( 500 )

#Save data
save_data = True
folder_label = f"T2_spectrum"


if save_data: 
    from exp.save_data import DataPackager
    save_dir = link_config["path"]["output_root"]
    dp = DataPackager( save_dir, folder_label )
    dp.save_config(config)
    dp.save_nc(dataset,folder_label)

# Plot
save_figure = 1
# dataset = xr.open_dataset(r"C:\Users\quant\SynologyDrive\09 Data\Fridge Data\Qubit\20240711_DR3_5Q4C_0430#7\good\20240713_1816_find_ZZfree_q1_q2.nc")
fig = plot_pureZZ(dataset)
if save_figure: dp.save_fig( fig, folder_label )
plt.show()


