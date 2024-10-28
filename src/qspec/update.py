
from config_component.configuration import Configuration
from qspec.envelope_builder import EnvelopeBuilder

import numpy as np
# ===================== Update about XY =====================================
### directly update the frequency info into config ### 
def update_controlFreq( config:Configuration, updatedInfo:dict ):
    """
        Only update the info in config about control frequency\n
        updatedInfo: from `Circuit_info.update_axyInfo_for()`
    """
    for info in updatedInfo:
        print(info)
        if info.split("_")[1].lower() in ["lo","if"]: # this should be update in both elements and mixers
            target_q = info.split("_")[-1]
            target_q_idx = int(target_q[1:])
            element_name = f"{target_q}_xy"
            element = config.elements[element_name]
            mixer_name = element.input_map.mixer
            mixer = config.mixers[mixer_name]
            # print(mixer.iFChannels)
            # update LO or IF in elements and mixers
            # TODO target_q_idx should replace 0
            if info.split("_")[1] == "LO":
                element.input_map.lo_frequency = updatedInfo[info]
                mixer.iFChannels[0].lo_frequency = updatedInfo[info]
            else: 
                element.intermediate_frequency = updatedInfo[info]
                mixer.iFChannels[0].intermediate_frequency = updatedInfo[info]
            
        else: 
            raise KeyError("Only surpport update frequenct related info to config!")

### update amp, len,...etc need an updated spec to re-build the waveform ###
def update_controlWaveform(config:Configuration,updatedSpec:dict={},target_q:str="all",**kwargs):
    '''
        If the spec about control had been updated need to re-build the waveforms in the config.\n
        A updated spec is given and call the EnvelopeBuilder class re-build the config.\n
        Give the specific target qubit "q1" to update if it's necessary, default for all the qubits.\n
        kwargs for assign update constant wf or saturation wf, USE: other=True/False.
    '''
    if updatedSpec == {}:
        raise ValueError("The updated spec should be given!")
    qs = [target_q] if target_q != 'all' else updatedSpec["register"]
    for q in qs:
        waveform_remaker = EnvelopeBuilder(xyInfo=updatedSpec[q])
        element_name = f"{q}_xy"
        print(f"{q} update controlWaveform")
        # Default constant pulse
        config.waveforms[f"{element_name}_const_wf"].sample = updatedSpec[q]["const_amp"]

        for opration in config.elements[element_name].operations: 
            
           
            pulse_name = f"{element_name}_{opration}_pulse"
            # Single Q operation
            if opration in ["x180", "-x180", "y180", "x90", "-x90", "y90", "-y90", "multisin"]: 
                conv_table = {
                    "x180": "x",
                    "-x180": "-x",
                    "y180": "y",
                    "x90": "x/2",
                    "-x90": "-x/2",
                    "y90": "y/2",
                    "-y90": "-y/2",
                    "xmultisin": "xmultisin"
                }
                waveform_remaker.QsXyInfo = updatedSpec[q]
                wf = waveform_remaker.build_XYwaveform(target_q=q,axis=conv_table[opration])
                for if_port in ["I","Q"]:
                    waveform_name = f"{element_name}_{opration}_wf_{if_port}"
                    config.waveforms[waveform_name].sample = wf[if_port].tolist()
                # pi_len check
                config.pulses[pulse_name].length = updatedSpec[q]['pi_len']


# ================= Update about Z ===================================
def update_z_offset(config:Configuration,zInfo:dict,wire:dict,mode:str="offset"):
    '''
        update the z offset in config controllers belongs to the target qubit.\n
        zInfo is the dict belongs to the target qubit returned by the func. `Circuit_info().update_zInfo_for()`\n
        mode for select the z info: 'offset' for maximum qubit freq. 'OFFbias' for tuned qubit away from sweetspot. 'idle' for idle point.\n
    '''
    ctrler_name, channel = wire["z"]
    z_output = config.controllers[ctrler_name].analog_outputs

    if mode.lower() in ['offset','offbias','idle']:
        z_output[channel].offset = zInfo[mode]   
    else:
        raise ValueError("mode argument should be one of 'offset', 'OFFbias' or 'idle'!")       

def update_z_crosstalk(config:Configuration,zInfo:dict,wire:dict):
    '''
        update the z crosstalk in config controllers belongs to the target qubit.\n
        zInfo is the dict belongs to the target qubit returned by the func. `Circuit_info().update_zInfo_for()`\n
    '''
    ctrler_name, channel = wire["z"]
    z_output = config.controllers[ctrler_name].analog_outputs

    z_output[channel].crosstalk = zInfo["crosstalk"]   
   

def update_zWaveform(config,updatedZspec:dict,target_q:str="all"):
    """
        Update the waveforms about 'const_flux_wf' in config.waveforms by the given updated z spec.
    """

    if updatedZspec == {}:
        raise ValueError("The updated spec should be given!")
        
    qs = [target_q] if target_q != 'all' else updatedZspec["register"]
    for q in qs:
        waveform_remaker = EnvelopeBuilder(zInfo=updatedZspec[q])
        element_name = f"{q}_z"
        print(f"{q} update controlWaveform")
        # Default constant pulse
        config.waveforms[f"{element_name}_const_wf"].sample = updatedZspec[q]["z_amp"]
        config.pulses[f"{element_name}_const_pulse"].length = updatedZspec[q]['z_len']
        for opration in config.elements[element_name].operations: 
            
            pulse_name = f"{element_name}_{opration}_pulse"
            # Single Q operation
            if opration in ["sin"]: 
                conv_table = {
                    "sin": "sin",
                }
                wf = waveform_remaker.build_zWaveform(axis=conv_table[opration])
                waveform_name = f"{q}_z_{opration}_wf"
                config.waveforms[waveform_name].sample = wf.tolist()
                # pi_len check
                config.pulses[pulse_name].length = updatedZspec[q]['z_len']

def update_zWiring(config,target_q:str='all',updatedZspec:dict={}):
    """
        Update the z port for target q. target_q default for all qubits.
    """
    '''TODO'''
    pass


# ================= Update about RO =========================
def update_ReadoutFreqs(config:Configuration,updatedInfo:dict):
    '''
        Because frequency info only for mixers and elements,\n
        update the RO freq for dynamic configuration includes IF and LO.\n
        updatedInfo: from `Circuit_info.update_roInfo_for()`
    '''

    for info in updatedInfo:
        target_q = info.split("_")[-1]
        elements = config.elements[f'{target_q}_ro']
        mixer_name = elements.input_map.mixer
        match info.split("_")[1].lower():
            case 'if':
                elements.intermediate_frequency = updatedInfo[info]
                config.mixers[mixer_name].iFChannels[int(target_q[-1])].intermediate_frequency = updatedInfo[info]
            case 'lo' :
                elements.input_map.lo_frequency = updatedInfo[info]
                config.mixers[mixer_name].iFChannels[int(target_q[-1])].lo_frequency = updatedInfo[info]
            case _:
                raise KeyError(f"RO update keyname goes wrong: {info.split('_')[1].lower()}")
        

def update_Readout(config:Configuration,target_q:str='all',roInfo:dict={}, wiring:dict={}):
    """
        Beside frequency, other info will need to update the waveform or integration weights,\n
        update the other info for dynamic configuration like amp, len.... for the specific qubit\n
        target_q: "q3", default for all the qubits,\n
        updatedInfo: from `Circuit_info.roInfo`,\n
        integration_weights_from: which weights should be accepted 'origin', 'rotated' or 'optimal'
    """
    # Check readout pulse leneth is changed or not
    # Check time_of_flights is change or not
    qs = [target_q] if target_q != 'all' else roInfo["register"] 

    for q in qs:
        element_name = f'{q}_ro'
        wf_name = f'{element_name}_readout_wf'
        pulse_name = config.elements[element_name].operations["readout"]
        # if integration_weights_from.lower() in ['origin', 'rotated', 'optimal']:
        #     # integration Weight
        #     config.update_integrationWeight(target_q=q,updated_RO_spec=roInfo,from_which_value=integration_weights_from)        
        # pulses length
        config.pulses[pulse_name].length = roInfo[q]['readout_len']
        
        w_name = f"{q}_ro_rotated_weight_"
        config.integration_weights[w_name+"cos"].cosine = [(np.cos(roInfo[q]['rotated']),roInfo[q]['readout_len'])]
        config.integration_weights[w_name+"cos"].sine = [(np.sin(roInfo[q]['rotated']),roInfo[q]['readout_len'])]

        config.integration_weights[w_name+"sin"].cosine = [(-np.sin(roInfo[q]['rotated']),roInfo[q]['readout_len'])]
        config.integration_weights[w_name+"sin"].sine = [(np.cos(roInfo[q]['rotated']),roInfo[q]['readout_len'])]

        config.integration_weights[w_name+"minus_sin"].cosine = [(np.sin(roInfo[q]['rotated']),roInfo[q]['readout_len'])]
        config.integration_weights[w_name+"minus_sin"].sine = [(-np.cos(roInfo[q]['rotated']),roInfo[q]['readout_len'])]

        con_I_name, ch_I_idx = wiring[q]["rin_I"]
        con_Q_name, ch_Q_idx = wiring[q]["rin_Q"]
        # print(roInfo[q]['offset'], (con_I_name, ch_I_idx), (con_Q_name, ch_Q_idx),config.controllers[con_I_name].analog_inputs)
        config.controllers[con_I_name].analog_inputs[ch_I_idx]["offset"] = roInfo[q]['offset'][0]      
        config.controllers[con_Q_name].analog_inputs[ch_Q_idx]["offset"] = roInfo[q]['offset'][1]      


        # time_of_flights
        config.elements[element_name].time_of_flight = roInfo[q]['time_of_flight']        
        # waveforms values
        config.waveforms[wf_name].sample = roInfo[q]['readout_amp']
    print('RO dynamic config secessfully updated!')