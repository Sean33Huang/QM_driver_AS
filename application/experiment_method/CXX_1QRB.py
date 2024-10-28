from pathlib import Path
link_path = Path(__file__).resolve().parent.parent/"config_api"/"config_link.toml"

from QM_driver_AS.ultitly.config_io import import_config, import_link
link_config = import_link(link_path)
config_obj, spec = import_config( link_path )

config = config_obj.get_config()
qmm, _ = spec.buildup_qmm()

from ab.QM_config_dynamic import initializer

import matplotlib.pyplot as plt

from exp.randomized_banchmarking_sq import randomized_banchmarking_sq

my_exp = randomized_banchmarking_sq(config, qmm)
my_exp.initializer = initializer(100000,mode='wait')

# pi_len = the_specs.get_spec_forConfig('xy')['q1']['pi_len']
my_exp.gate_length = 40
##############################
# Program-specific variables #
##############################
my_exp.xy_elements = ["q3_xy","q4_xy"]
my_exp.ro_elements = ["q3_ro","q4_ro"]
# threshold = the_specs.get_spec_forConfig('ro')[xy_element]['ge_threshold']

my_exp.n_avg = 40  # Number of averaging loops for each random sequence
my_exp.max_circuit_depth = 200  # Maximum circuit depth
my_exp.delta_clifford = 1  #  Play each sequence with a depth step equals to 'delta_clifford - Must be > 1
assert (my_exp.max_circuit_depth / my_exp.delta_clifford).is_integer(), "max_circuit_depth / delta_clifford must be an integer."
my_exp.seed = 345324  # Pseudo-random number generator seed

# Flag to enable state discrimination if the readout has been calibrated (rotated blobs and threshold)
# state_discrimination = [1e-3]
dataset = my_exp.run(20)

save_data = 1
folder_label = "1QRB" #your data and plots will be saved under a new folder with this name

if save_data: 
    from exp.save_data import DataPackager
    save_dir = link_config["path"]["output_root"]
    dp = DataPackager( save_dir, folder_label )
    dp.save_config(config)
    dp.save_nc(dataset,"1QRB")

from exp.plotting import Painter1QRB
painter = Painter1QRB()
figs = painter.plot(dataset,folder_label)
if save_data: dp.save_figs( figs )

# plot_SQRB_result( x, value_avg, error_avg )

# plt.show()