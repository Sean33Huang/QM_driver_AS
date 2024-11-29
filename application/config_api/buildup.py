
cluster_name = "QPX_3"  # Write your cluster_name if version >= QOP220
qop_ip = "192.168.1.9"  # Write the QM router IP address
qop_port = None 

# Default
port_mapping = {
("con1", 1): ("octave1", "I1"),
("con1", 2): ("octave1", "Q1"),
("con1", 3): ("octave1", "I2"),
("con1", 4): ("octave1", "Q2"),
("con1", 5): ("octave1", "I3"),
("con1", 6): ("octave1", "Q3"),
("con1", 7): ("octave1", "I4"),
("con1", 8): ("octave1", "Q4"),
("con1", 9): ("octave1", "I5"),
("con1", 10): ("octave1", "Q5"),

# ("con2", 1): ("octave2", "I1"),
# ("con2", 2): ("octave2", "Q1"),
# ("con2", 3): ("octave2", "I2"),
# ("con2", 4): ("octave2", "Q2"),
# ("con2", 5): ("octave2", "I3"),
# ("con2", 6): ("octave2", "Q3"),
# ("con2", 7): ("octave2", "I4"),
# ("con2", 8): ("octave2", "Q4"),
# ("con2", 9): ("octave2", "I5"),
# ("con2", 10): ("octave2", "Q5"),
}

qubit_num = 9

from qspec.channel_info import ChannelInfo
spec = ChannelInfo(qubit_num)

# Set QMM
spec.update_HardwareInfo(qop_ip=qop_ip, qop_port=qop_port, cluster_name=cluster_name)
# Set Octave
spec.update_octave( "octave1", ip=qop_ip, port=11253, con="con1", port_map=port_mapping, clock="Internal")

# Only for opx+
opxp_hardware = {
    "analog_outputs": {
        1: {"offset": 0.0},  # I readout line
        2: {"offset": 0.0},  # Q readout line
        3: {"offset": 0.0},  # I qubit1 XY
        4: {"offset": 0.0},  # Q qubit1 XY
        5: {"offset": 0.0},  # I qubit2 XY
        6: {"offset": 0.0},  # Q qubit2 XY
        7: {"offset": 0.0},  # I qubit3 XY
        8: {"offset": 0.0},  # Q qubit3 XY
        9: {"offset": 0.0},  # I qubit4 XY
        10: {"offset": 0.0},  # Q qubit4 XY
    },
    "digital_outputs": {
        1: {},
        3: {},
        5: {},
        7: {},
        9: {},
    },
    "analog_inputs": {
        1: {"offset": 0, "gain_db": 0},  # I from down-conversion
        2: {"offset": 0, "gain_db": 0},  # Q from down-conversion
    },
}

# Only for octave
LO = 6e9
octave_hardware = {
    "RF_outputs": {
        1: {
            "LO_frequency": LO,
            "LO_source": "internal",  # can be external or internal. internal is the default
            "output_mode": "always_on",  # can be: "always_on" / "always_off"/ "triggered" / "triggered_reversed". "always_off" is the default
            "gain": 0,  # can be in the range [-20 : 0.5 : 20]dB
        },
        2: {
            "LO_frequency": LO,
            "LO_source": "internal",
            "output_mode": "always_on",
            "gain": 0,
        },
        3: {
            "LO_frequency": LO,
            "LO_source": "internal",
            "output_mode": "always_on",
            "gain": 0,
        },
        4: {
            "LO_frequency": LO,
            "LO_source": "internal",
            "output_mode": "always_on",
            "gain": 0,
        },
        5: {
            "LO_frequency": LO,
            "LO_source": "internal",
            "output_mode": "always_on",
            "gain": 0,
        },
    },
    "RF_inputs": {
        1: {
            "LO_frequency": LO,
            "LO_source": "internal",  # internal is the default
            "IF_mode_I": "direct",  # can be: "direct" / "mixer" / "envelope" / "off". direct is default
            "IF_mode_Q": "direct",
        },
        2: {
            "LO_frequency": LO,
            "LO_source": "external",  # external is the default
            "IF_mode_I": "direct",
            "IF_mode_Q": "direct",
        },
    },
    "connectivity": "con1",
}

from config_component.configuration import Configuration
config_obj = Configuration()

# Create controller
from config_component.controller import controller_read_dict
config_obj._controllers["con1"] = controller_read_dict("con1", opxp_hardware)
# config_obj._controllers["con2"] = controller_read_dict("con2", opxp_hardware)

# Create octave
from config_component.octave import octave_read_dict
config_obj._octaves["octave1"] = octave_read_dict("octave1", octave_hardware)


# Create qubit
from qspec.construct import create_qubit, create_roChannel, create_zChannel, create_xyChannel

for x_wire in [("q0",("con1",3),("con1",4)),("q1",("con1",7),("con1",8)), ("q2",("con1",3),("con1",4)),("q3",("con1",7),("con1",8)), ("q4",("con1",3),("con1",4)), ("q5",("con1",3),("con1",4)),("q6",("con1",7),("con1",8)), ("q7",("con1",3),("con1",4)),("q8",("con1",7),("con1",8))]:
    spec.update_WireInfo_for(x_wire[0],xy_I=x_wire[1],xy_Q=x_wire[2])

for z_wire in [("q0",("con1",5)),("q1",("con1",6)),("q2",("con1",9)),("q3",("con1",10)),("q4",("con1",5)), ("q5",("con1",9)),("q6",("con1",10)),("q7",("con1",5)), ("q8",("con1",6))]:
    spec.update_WireInfo_for(z_wire[0],z=z_wire[1])

for q_idx in range(qubit_num):
    q_name = f"q{q_idx}"
    create_qubit( config_obj,q_name,spec.get_spec_forConfig('ro'),spec.get_spec_forConfig('xy'),spec.get_spec_forConfig('wire'),spec.get_spec_forConfig('z'))


from pathlib import Path
# Get the current file path
current_file = Path(__file__).resolve()
# Get the parent directory
link_path = current_file.parent/"config_link.toml"

from QM_driver_AS.ultitly.config_io import output_config
output_config( link_path, config_obj, spec )