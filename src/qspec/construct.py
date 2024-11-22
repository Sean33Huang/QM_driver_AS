from config_component.controller import Controller, controller_read_dict
from config_component.element import Element, element_read_dict
from config_component.pulse import Pulse, pulse_read_dict
from config_component.waveform import Waveform, waveform_read_dict
from config_component.digital_waveform import DigitalWaveform, digitalWaveform_read_dict
from config_component.integration_weight import IntegrationWeights, integrationWeight_read_dict
from config_component.mixer import Mixer, mixer_read_list
from config_component.configuration import Configuration

def create_roChannel( config:Configuration, name, roInfo:dict, wireInfo:dict ):
    """
    element structure \n
    """
    pulse_name = f"{name}_readout_pulse"
    waveform_name = f"{name}_readout_wf"
    # Build Element
    element = Element(name, input_type="mixInputs")
    element.input_map.I = wireInfo["rin_I"]
    element.input_map.Q = wireInfo["rin_Q"]
    element.input_map.lo_frequency = roInfo["resonator_LO"]
    element.input_map.mixer = wireInfo["ro_mixer"]
    element.operations["readout"] = pulse_name
    element.intermediate_frequency = roInfo["resonator_IF"]

    element.output_map["out1"] = wireInfo["rout_I"]
    element.output_map["out2"] = wireInfo["rout_Q"]
    element.time_of_flight = roInfo["time_of_flight"]
    element._smearing = 0
    # Build Pulse
    pulse = Pulse(pulse_name)
    pulse.operation = "measurement"
    pulse.length = 2000
    pulse.waveforms.I = waveform_name
    pulse.waveforms.Q = "zero_wf"
    pulse._digital_marker = "ON"
    
    # Build Mixer TODO check previous mixer status for other qubit, final one will cover others
    mixer_name = element.input_map.mixer
    mixer = Mixer(mixer_name)
    from config_component.mixer import IFChannel
    iFChannel = IFChannel()
    iFChannel._lo_frequency = element.input_map.lo_frequency
    iFChannel._intermediate_frequency = element.intermediate_frequency
    iFChannel._correction = (1, 0, 0, 1)
    
    if mixer_name in config._mixers.keys():
        config._mixers[mixer_name]._iFChannels.append( iFChannel )
    else: # the mixer not exist yet
        mixer._iFChannels.append( iFChannel )
        config._mixers[mixer_name] = mixer

    # Build waveform
    waveform = Waveform(waveform_name)
    waveform.type = "constant"
    waveform.sample = roInfo["readout_amp"]     

    # Build intergration weight   
    integ_name = f"{name}_rotated_weight"
    integ_len = pulse.length
    for weight_name, cos_w, sin_w in zip(["cos", "sin", "minus_sin"],[1,0,0],[0,1,-1]):
        complete_integ_name = f"{integ_name}_{weight_name}"
        integration_weight_obj = IntegrationWeights(complete_integ_name)
        integration_weight_obj._cosine = [(cos_w,integ_len)]
        integration_weight_obj._sine = [(sin_w,integ_len)]

        pulse.integration_weights[f"rotated_{weight_name}"] = complete_integ_name           
        config._integration_weights[complete_integ_name] = integration_weight_obj

    config._elements[name] = element
    config._pulses[pulse_name] = pulse
    config._waveforms[waveform_name] = waveform

def create_zChannel(config:Configuration, name:str, zInfo:dict, wireInfo:dict):
    """
        create the z elements for target_q, includes elements, pulses, waveforms.
    """  

    pulse_name = f"{name}_const_pulse"
    waveform_name = f"{name}_const_wf"

    default_native_gates = ["sin"]
    # elements value
    element = Element( name, input_type="singleInput" )
    element.input_map.port = wireInfo["z"]
    element.operations = {
        "const": pulse_name,
    }

    # pulses value
    pulse = Pulse(pulse_name)
    pulse.operation = "control"
    pulse.length = zInfo["z_len"]
    pulse.waveforms.single = waveform_name
    config._pulses[pulse_name] = pulse

    # waveforms value
    waveform = Waveform(waveform_name)
    waveform.type = "constant"
    waveform.sample = zInfo['z_amp']
    config._waveforms[waveform_name] = waveform

    # elements name
    config._elements[name] = element
    
    from qspec.envelope_builder import EnvelopeBuilder
    wave_maker = EnvelopeBuilder(zInfo=zInfo)

    for gate_name in default_native_gates:
        pulse_name = f"{name}_{gate_name}_pulse"
        waveform_name = f"{name}_{gate_name}_wf"

        element.operations[gate_name] = pulse_name

        pulse = Pulse(pulse_name)
        pulse.operation = "control"
        pulse.length = zInfo[f"z_len"]
        pulse.waveforms.single = f"{waveform_name}"

        config._pulses[pulse_name] = pulse

        match gate_name:
            case "sin": a = "sin"
            case _: a = None

        # Create waveform list, if spec is updated it also need to be updated
        wf = wave_maker.build_zWaveform(axis=a)
        waveform = Waveform(waveform_name)
        waveform.type = "arbitrary"
        waveform.sample = wf.tolist()
        config._waveforms[waveform_name] = waveform
    

def create_xyChannel(config:Configuration, name, xyInfo:dict, wireInfo:dict):
    """
    name : "q2_xy"..\n
    element ex:\n
    \n

    xyInfo is from Circuit_info().xyInfo\n
    Native gates ["x180","y180","x90","-x90","y90","-y90"]
    """
    pulse_name = f"{name}_const_pulse"
    waveform_name = f"{name}_const_wf"

    default_native_gates = [ "x180","-x180","y180","-y180","x90","-x90","y90","-y90" ]
    element = Element(name, "mixInputs")
    element.input_map.I = wireInfo["xy_I"]
    element.input_map.Q = wireInfo["xy_Q"]
    element.input_map.lo_frequency = xyInfo["qubit_LO"]
    element.input_map.mixer = wireInfo["xy_mixer"]
    element.intermediate_frequency = xyInfo["qubit_IF"]

    element.operations = {
        "const": pulse_name,
    }
        

    # Create the mixer info for control
    mixer_name = element.input_map.mixer
    mixer = Mixer(mixer_name)
    from config_component.mixer import IFChannel
    iFChannel = IFChannel()
    iFChannel.intermediate_frequency = element.intermediate_frequency
    iFChannel.lo_frequency = element.input_map.lo_frequency
    iFChannel.correction= (1, 0, 0, 1)
    mixer.iFChannels.append(iFChannel)
    config._mixers[mixer_name] = mixer

    # create corresponding waveform name in pulses dict, create waveform list in waveforms dict
    from qspec.envelope_builder import EnvelopeBuilder
    wave_maker = EnvelopeBuilder(xyInfo=xyInfo)
    waveform = Waveform(waveform_name)
    waveform.type = "constant"
    waveform.sample = xyInfo["const_amp"]
    config._waveforms[waveform_name] = waveform

    pulse = Pulse(pulse_name)
    pulse.operation = "control"
    pulse.length = xyInfo["const_len"]
    pulse.waveforms.I = waveform_name
    pulse.waveforms.Q = "zero_wf"
    config._pulses[pulse_name] = pulse

    for gate_name in default_native_gates:

        pulse_name = f"{name}_{gate_name}_pulse"
        waveform_name = f"{name}_{gate_name}_wf"

        element.operations[gate_name] = pulse_name

        pulse = Pulse(pulse_name)
        pulse.operation = "control"
        pulse.length = xyInfo[f"pi_len"]
        pulse.waveforms.I = f"{waveform_name}_I"
        pulse.waveforms.Q = f"{waveform_name}_Q"

        config._pulses[pulse_name] = pulse

        match gate_name:
            case "x180": a = "x"
            case "-x180": a = "-x"
            case "y180": a = "y"
            case "-y180": a = "-y"
            case "x90": a = "x/2"
            case "-x90": a = "-x/2"
            case "y90": a = "y/2"
            case "-y90": a = "-y/2"
            case _: a = None
        # Create waveform list, if spec is updated it also need to be updated
        wf = wave_maker.build_XYwaveform(axis=a)
        for waveform_basis in ["I","Q"]:
            ''' waveform_basis is "I" or "Q" '''
            new_wf_name = f"{waveform_name}_{waveform_basis}"
            waveform = Waveform(new_wf_name)
            waveform.type = "arbitrary"
            waveform.sample = wf[waveform_basis].tolist()
            config._waveforms[new_wf_name] = waveform
    
    config._elements[name] = element

def create_qubit( config:Configuration, name:str, roInfo:dict, xyInfo:dict, wireInfo:dict, zInfo:dict, **kwargs):
    """
    name : "q3",\n
    roInfo
        "ro_IF","ro_LO","electrical_delay","integration_time","ro_wf"
    
    xyInfo
    keys
    "pi_amp","pi_len","qubit_LO","qubit_IF","drag_coef","anharmonicity","AC_stark_detuning","waveform_func"
    
    """        
    # Build RO
    create_roChannel( config, f"{name}_ro", roInfo[name], wireInfo[name])

    # Build XY
    create_xyChannel( config, f"{name}_xy", xyInfo[name], wireInfo[name])

    # Build Z line
    create_zChannel( config, f"{name}_z", zInfo[name], wireInfo[name] )

# Control related shows below


