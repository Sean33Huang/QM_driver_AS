# -------------- import  -------------- 
from pathlib import Path
link_path = Path(__file__).resolve().parent.parent/"config_api"/"config_link.toml"

from QM_driver_AS.ultitly.config_io import import_config, import_link
link_config = import_link(link_path)
config_obj, spec = import_config( link_path )

from qspec.update import update_controlWaveform
from QM_driver_AS.ultitly.config_io import output_config

from QM_driver_AS.ultitly.set_octave import ElementsSettings, octave_settings

from exp.randomized_banchmarking_sq import randomized_banchmarking_sq
from exp.randomized_banchmarking_interleaved_sq import randomized_banchmarking_interleaved_sq
from ab.QM_config_dynamic import initializer

# -------------- Needed function ------------------
import numpy as np
def power_law(power, a, b, p):
    return a * (p**power) + b

def ana_SQRB(x, y ):
    from scipy.optimize import curve_fit
    pars, cov = curve_fit(
        f=power_law,
        xdata=x,
        ydata=y,
        p0=[-0.0001, 0.0001, 0.0001],
        bounds=(-np.inf, np.inf),
        maxfev=2000,
    )
    stdevs = np.sqrt(np.diag(cov))

    print("#########################")
    print("### Fitted Parameters ###")
    print("#########################")
    print(f"A = {pars[0]:.3} ({stdevs[0]:.1}), B = {pars[1]:.3} ({stdevs[1]:.1}), p = {pars[2]:.3} ({stdevs[2]:.1})")
    print("Covariance Matrix")
    print(cov)

    one_minus_p = 1 - pars[2]
    r_c = one_minus_p * (1 - 1 / 2**1)
    r_g = r_c / 1.875  # 1.875 is the average number of gates in clifford operation
    r_c_std = stdevs[2] * (1 - 1 / 2**1)
    r_g_std = r_c_std / 1.875

    print("#########################")
    print("### Useful Parameters ###")
    print("#########################")
    print(
        f"Error rate: 1-p = {np.format_float_scientific(one_minus_p, precision=2)} ({stdevs[2]:.1})\n"
        f"Clifford set infidelity: r_c = {np.format_float_scientific(r_c, precision=2)} ({r_c_std:.1})\n"
        f"Gate infidelity: r_g = {np.format_float_scientific(r_g, precision=2)}  ({r_g_std:.1})"
    )
    
    return stdevs, pars, one_minus_p, r_c, r_g, r_c_std, r_g_std

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
# -------------- Initial parameters ------------------
target_q = 'q3'
target_gate_index = 2 
## Gate intex to gate
## 0 = I
## 1 = x180
## 2 = y180
## 12 = x90
## 13 = -x90
## 14 = y90
## 15 = -y90

pi_amp=  0.1114941471
drag_coef = 0.03

# -------------- Goal function ------------------
# prepare parameters
init_params = [pi_amp, drag_coef,]

# Settings of infidelity measurement
gate_length = 40

n_avg = 50  # Number of averaging loops for each random sequence
max_circuit_depth = 1024  # Maximum circuit depth
base_clifford = 2  #  Play each sequence with a depth step equals to 'delta_clifford - Must be > 1
assert base_clifford > 1, 'base must > 1'
seed = 345324  # Pseudo-random number generator seed
interleaved_gate_index = 2
same_seq = True
shot_num = 50

qmm, octaves = spec.buildup_qmm()
config = config_obj.get_config()

def goal_function(init_params):

    amp = init_params[0]
    draga = init_params[1]
    # Update XY
    spec.update_aXyInfo_for(target_q=target_q, 
                            amp=amp, 
                            draga=draga, 
                            )
    update_controlWaveform(config_obj, spec.get_spec_forConfig("xy"), target_q=target_q )
    output_config( link_path, config_obj, spec )

    # Octave calibration
    # qmm, octaves = spec.buildup_qmm()
    # config = config_obj.get_config()
    # elements_settings = [ElementsSettings(f"{target_q}_xy")]
    # octave_settings(
    #     qmm=qmm,
    #     config=config,
    #     octaves=octaves,
    #     elements_settings=elements_settings,
    #     calibration=True,
    # )
    # qmm.close()

    # Measure infidelity
    config = config_obj.get_config()
    qmm, _ = spec.buildup_qmm()

    my_exp = randomized_banchmarking_sq(config, qmm)
    my_exp.initializer = initializer(100000,mode='wait')
    my_exp.gate_length = gate_length
    my_exp.xy_elements = [f"{target_q}_xy"]
    my_exp.ro_elements = [f"{target_q}_ro"]
    # my_exp.threshold = threshold
    my_exp.n_avg = n_avg
    my_exp.max_circuit_depth = max_circuit_depth 
    my_exp.base_clifford = base_clifford
    my_exp.seed = seed 
    dataset = my_exp.run(shot_num)

    my_exp = randomized_banchmarking_interleaved_sq(config, qmm)
    my_exp.initializer = initializer(100000,mode='wait')
    my_exp.gate_length = gate_length
    my_exp.xy_elements = [f"{target_q}_xy"]
    my_exp.ro_elements = [f"{target_q}_ro"]
    # my_exp.threshold = threshold
    my_exp.n_avg = n_avg
    my_exp.max_circuit_depth = max_circuit_depth 
    my_exp.base_clifford = base_clifford
    my_exp.seed = seed 
    my_exp.interleaved_gate_index = interleaved_gate_index
    dataset_interleaved = my_exp.run(shot_num)

    data1 = dataset.data_vars[f"{target_q}_ro"]
    data2 = dataset_interleaved.data_vars[f"{target_q}_ro"]

    x = data1.coords["x"].values
    val = data1.values[0]
    err = data1.values[1]
    val_inl = data2.values[0]
    err_inl = data2.values[1]

    stdevs, pars, one_minus_p, r_c, r_g, r_c_std, r_g_std = ana_SQRB( x, val )
    stdevs_inl, pars_inl, one_minus_p_inl, r_c_inl, r_g_inl, r_c_std_inl, r_g_std_inl = ana_SQRB( x, val_inl )

    return 1-pars_inl[2]/pars[2]

# -------------- Optimization
from scipy.optimize import minimize

optimization_trace = {"amp": [], "draga": [], "infidelity": []}

def callback(init_params):
    a0 = init_params[0]
    a1 = init_params[1]
    f_val = goal_function(init_params)
    optimization_trace["amp"].append(a0)
    optimization_trace["draga"].append(a1)
    optimization_trace["infidelity"].append(f_val)

result = minimize(goal_function, init_params, method='Nelder-Mead', 
                  options={'maxiter': 20, 'maxfev': 50, 'disp': True},
                  callback=callback)

import xarray as xr

dataset = xr.Dataset(
    {"objective_values": (["iteration"], optimization_trace["infidelity"])},
    coords={
        "iteration": np.arange(len(optimization_trace["infidelity"])),
        "amp": ("iteration", optimization_trace["amp"]),
        "draga": ("iteration", optimization_trace["draga"]),
    }
)
save_data = 1
folder_label = f"1QRB_{get_interleaved_gate(target_gate_index)}_optimization" #your data and plots will be saved under a new folder with this name

if save_data: 
    from exp.save_data import DataPackager
    save_dir = link_config["path"]["output_root"]
    dp = DataPackager( save_dir, folder_label )
    dp.save_config(config)
    dp.save_nc(dataset,"1QRB")

print(dataset)
# 輸出結果
print("Best gate parameers :", result.x)
print("Best gate infidelity", result.fun)