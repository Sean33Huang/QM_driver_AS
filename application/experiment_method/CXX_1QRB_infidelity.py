from pathlib import Path
link_path = Path(__file__).resolve().parent.parent/"config_api"/"config_link.toml"

from QM_driver_AS.ultitly.config_io import import_config, import_link
link_config = import_link(link_path)
config_obj, spec = import_config( link_path )

config = config_obj.get_config()
qmm, _ = spec.buildup_qmm()

from ab.QM_config_dynamic import initializer

##############################
# Program-specific variables #
##############################
gate_length = 40
xy_elements = ["q3_xy"]
ro_elements = ["q3_ro"]

n_avg = 100  # Number of averaging loops for each random sequence
max_circuit_depth = 1024  # Maximum circuit depth
base_clifford = 2  #  Play each sequence with a depth step equals to 'delta_clifford - Must be > 1
assert base_clifford > 1, 'base must > 1'
seed = 345324  # Pseudo-random number generator seed
interleaved_gate_index = 2
## Gate intex to gate
## 0 = I
## 1 = x180
## 2 = y180
## 12 = x90
## 13 = -x90
## 14 = y90
## 15 = -y90
shot_num = 500
# Flag to enable state discrimination if the readout has been calibrated (rotated blobs and threshold)
state_discrimination = True
threshold = 2.016e-05

# ------------------------------------------------------------
from exp.randomized_banchmarking_sq import randomized_banchmarking_sq

my_exp = randomized_banchmarking_sq(config, qmm)
my_exp.initializer = initializer(200000,mode='wait')
my_exp.gate_length = gate_length
my_exp.xy_elements = xy_elements
my_exp.ro_elements = ro_elements
my_exp.n_avg = n_avg
my_exp.max_circuit_depth = max_circuit_depth 
my_exp.base_clifford = base_clifford
assert my_exp.base_clifford > 1, 'base must > 1'
my_exp.seed = seed 
my_exp.state_discrimination = state_discrimination
my_exp.threshold = threshold
dataset = my_exp.run(shot_num)

from exp.randomized_banchmarking_interleaved_sq import randomized_banchmarking_interleaved_sq

my_exp = randomized_banchmarking_interleaved_sq(config, qmm)
my_exp.initializer = initializer(200000,mode='wait')
my_exp.gate_length = gate_length
my_exp.xy_elements = xy_elements
my_exp.ro_elements = ro_elements
my_exp.n_avg = n_avg
my_exp.max_circuit_depth = max_circuit_depth 
my_exp.base_clifford = base_clifford
assert my_exp.base_clifford > 1, 'base must > 1'
my_exp.seed = seed 
my_exp.interleaved_gate_index = interleaved_gate_index
my_exp.state_discrimination = state_discrimination
my_exp.threshold = threshold
dataset_interleaved = my_exp.run(shot_num)

save_data = 1
folder_label = "1QRB_infedelity" #your data and plots will be saved under a new folder with this name

if save_data: 
    from exp.save_data import DataPackager
    save_dir = link_config["path"]["output_root"]
    dp = DataPackager( save_dir, folder_label )
    dp.save_config(config)
    dp.save_nc(dataset,"1QRB")
    dp.save_nc(dataset_interleaved,"1QRB_interleaved")

from exp.plotting import Painter1QRBInfidelity
painter = Painter1QRBInfidelity()
painter.state_discrimination = my_exp.state_discrimination
painter.interleaved_gate_index = my_exp.interleaved_gate_index
figs = painter.plot(dataset,folder_label,infidelity=dataset_interleaved)
if save_data: dp.save_figs( figs )

# plot_SQRB_result( x, value_avg, error_avg )

# plt.show()