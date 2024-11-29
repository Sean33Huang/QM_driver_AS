
from pathlib import Path
link_path = Path(__file__).resolve().parent/"config_link.toml"

from QM_driver_AS.ultitly.config_io import import_config
config_obj, spec = import_config( link_path )

from qspec.update import update_z_offset, update_z_crosstalk, update_z_filter, update_zWaveform

# [[ 0.99954093  0.00685605 -0.01088031 -0.01185879 -0.01199802]
#  [ 0.02307034  0.99941776 -0.01729353 -0.01564188 -0.01406762]
#  [ 0.01713722  0.01930098  0.99897034 -0.02075049 -0.01185133]
#  [ 0.02022993  0.01678385  0.01898975  0.99923273 -0.02882381]
#  [ 0.01681398  0.01113205  0.00966305 -0.00497131  0.99965561]]

z_infos = {
    "q0":{
        "offset": 0.0805,
        "crosstalk":{},
        "filter": {'feedforward': [], 'feedback':[]},
        "z_wf":"sin",
        "z_amp": 0.2,
        "z_len": 1000,
        "z_wf": "sin",
        "z_freq": 5.0,
        "z_phase": 0,
    },
    "q1":{
        "offset": -0.07,
        "crosstalk":{},
        "z_amp": 0.14,  
        "z_len": 10000,
        "z_wf": "sin",
        "z_freq": 500.0,   
        "z_phase": 30,
    }
    "q2":{
        "offset": 0.071,
        "crosstalk":{},
        "z_amp": 0.1,
        "z_len": 1000,
    },
    "q3":{
        "offset": 0.062,
        "crosstalk":{},
        "z_amp": 0.1,
        "z_len": 1000,
    },
    "q4":{
        "offset": 0.0,
        "crosstalk":{},
        "z_amp": 0.1,
        "z_len": 1000,
    },
    "q5":{
        "offset": 0.0,#0.152,
        "crosstalk":{},
        "z_amp": 0.1,
        "z_len": 1000,
    },
    "q6":{
        "offset": 0.0,
        "crosstalk":{},
        "z_amp": 0.1,
        "z_len": 1000,
    },
    "q7":{
        "offset": 0.067,
        "crosstalk":{},
        "z_amp": 0.1,
        "z_len": 1000,
    },
    "q8":{
        "offset": 0.0,
        "crosstalk":{},
        "z_amp": 0.1,
        "z_len": 1000,
    }
}
updating_qubit = ["q0","q1","q2","q3","q4","q5","q6","q7","q8"]

for i in updating_qubit:
    q_name = i
    wiring = spec.get_spec_forConfig('wire')

    z_wf = z_infos[i]["z_wf"] if "z_wf" in z_infos[i].keys() else "sin"
    z_amp = z_infos[i]["z_amp"] if "z_amp" in z_infos[i].keys() else 0.1
    z_len = z_infos[i]["z_len"] if "z_amp" in z_infos[i].keys() else 40
    z_freq = z_infos[i]["z_freq"] if "z_freq" in z_infos[i].keys() else 1
    z_phase = z_infos[i]["z_phase"] if "z_phase" in z_infos[i].keys() else 0

    # Tune Z offset
    z_info = spec.update_ZInfo_for(target_q=q_name,
                                   offset=z_infos[i]["offset"],
                                   crosstalk=z_infos[i]["crosstalk"],
                                   filter=z_infos[i]["filter"],
                                   wf=z_wf,
                                   amp=z_amp,
                                   len=z_len,
                                   freq=z_freq,
                                   phase=z_phase,
                                   )
    # print(wiring[i[0]])
    update_z_offset( config_obj, z_info, wiring[q_name], mode='offset')
    update_z_crosstalk( config_obj, z_info, wiring[q_name])
    update_z_filter( config_obj, z_info, wiring[q_name])
    update_zWaveform(config_obj, spec.get_spec_forConfig("z"), target_q=q_name )
    config_dict = config_obj.get_config() 


from QM_driver_AS.ultitly.config_io import output_config
output_config( link_path, config_obj, spec )