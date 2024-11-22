from pathlib import Path
link_path = Path(__file__).resolve().parent.parent/"config_api"/"config_link.toml"

from QM_driver_AS.ultitly.config_io import import_config, import_link
link_config = import_link(link_path)
config_obj, spec = import_config( link_path )

config = config_obj.get_config()
qmm, _ = spec.buildup_qmm()

from ab.QM_config_dynamic import initializer

# -------------- Needed function ------------------
import numpy as np
def power_law(power, a, p, b):
    return a * (p**power) + b

def ana_SQRB(x, y ):
    from scipy.optimize import curve_fit
    if state_discrimination == True:
        p0 = [-0.4, 1]
        def fit_func(power, a, p):
            return power_law(power, a, p, 0.5)
    else:
        p0=[-0.0001, 0.0001, 0.0001]
        def fit_func(power, a, p, b):
            return power_law(power, a, p, b)
    pars, cov = curve_fit(
        f=fit_func,
        xdata=x,
        ydata=y,
        p0=p0,
        bounds=(-np.inf, np.inf),
        maxfev=2000,
    )
    stdevs = np.sqrt(np.diag(cov))
    
    return stdevs, pars

def get_interleaved_gate(index):
        if index == 0:
            return "I"
        elif index == 1:
            return "x180"
        elif index == 2:
            return "y180"
        elif index == 12:
            return "x90"
        elif index == 13:
            return "-x90"
        elif index == 14:
            return "y90"
        elif index == 15:
            return "-y90"

##############################
# Program-specific variables #
##############################
gate_length = 40
xy_elements = ["q3_xy"]
ro_elements = ["q3_ro"]
target_q = 'q3'

n_avg = 100  # Number of averaging loops for each random sequence
max_circuit_depth = 1024  # Maximum circuit depth
base_clifford = 2  #  Play each sequence with a depth step equals to 'delta_clifford - Must be > 1
assert base_clifford > 1, 'base must > 1'
seed = 345324  # Pseudo-random number generator seed
interleaved_gate_index = 1
## Gate intex to gate
## 0 = I
## 1 = x180
## 2 = y180
## 12 = x90
## 13 = -x90
## 14 = y90
## 15 = -y90
shot_num = 100
# Flag to enable state discrimination if the readout has been calibrated (rotated blobs and threshold)
state_discrimination = True
threshold = 4.791e-05

amp_center = 0.04623571429
amp_shift = 0.01
amp_resolution = 0.001

# ------------------------------------------------------------
from exp.randomized_banchmarking_sq import randomized_banchmarking_sq
from exp.randomized_banchmarking_interleaved_sq import randomized_banchmarking_interleaved_sq
from qspec.update import update_controlWaveform
from QM_driver_AS.ultitly.config_io import output_config

def infidelity_func(amp):

    spec.update_aXyInfo_for(target_q=target_q, 
                            amp=amp, 
                            # ac=ac,
                            # wf=wf,
                            )
    update_controlWaveform(config_obj, spec.get_spec_forConfig("xy"), target_q=target_q )
    output_config( link_path, config_obj, spec )

    config = config_obj.get_config()
    qmm, _ = spec.buildup_qmm()

    my_exp = randomized_banchmarking_sq(config, qmm)
    my_exp.initializer = initializer(100000,mode='wait')
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

    my_exp = randomized_banchmarking_interleaved_sq(config, qmm)
    my_exp.initializer = initializer(100000,mode='wait')
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

    data1 = dataset.data_vars[f"{target_q}_ro"]
    data2 = dataset_interleaved.data_vars[f"{target_q}_ro"]

    x = data1.coords["x"].values
    val = data1.values[0]
    err = data1.values[1]
    val_inl = data2.values[0]
    err_inl = data2.values[1]

    stdevs, pars = ana_SQRB( x, val )
    stdevs_inl, pars_inl = ana_SQRB( x, val_inl )

    return (1 - pars_inl[1] / pars[1]) * (1 / 2**1 ), pars_inl[1]/pars[1] * ((stdevs[1]/pars[1])**2 + (stdevs_inl[1]/pars_inl[1])**2)**(1/2)

optimization_trace = {"infidelity": [],"error": []}
optimization_trace['amp'] = []
for amp in np.linspace(amp_center-amp_shift, amp_center+amp_shift, int(2*amp_shift/amp_resolution + 1)):
    f_val, err = infidelity_func(amp)
    optimization_trace["infidelity"].append(f_val)
    optimization_trace["error"].append(err)
    optimization_trace['amp'].append(amp)

# -------------- _data_formation -------------- 
import xarray as xr
output_data = {}
output_data[f"{target_q}_ro"] = (["mixer", 'amp'], 
                                 np.array([optimization_trace["infidelity"], 
                                           optimization_trace['error']]))
dataset = xr.Dataset(
    output_data,
    coords={
        "mixer": np.array(["infidelity",'error']),
        "amp": optimization_trace["amp"],
    }
)

save_data = 1
folder_label = "1QRB_infedelity_shift_one_param" #your data and plots will be saved under a new folder with this name

if save_data: 
    from exp.save_data import DataPackager
    save_dir = link_config["path"]["output_root"]
    dp = DataPackager( save_dir, folder_label )
    dp.save_config(config)
    dp.save_nc(dataset,folder_label)

from exp.plotting import Painter1QRB_infidelity_shift_one_param
painter = Painter1QRB_infidelity_shift_one_param()
painter.interleaved_gate_index = interleaved_gate_index
figs = painter.plot(dataset,folder_label)
if save_data: dp.save_figs( figs )

# plot_SQRB_result( x, value_avg, error_avg )

# plt.show()