from numpy import array

class EnvelopeBuilder:
    def __init__(self,xyInfo:dict={},zInfo:dict={}):
        ''' xyInfo, zInfo are the information inside a qubit
            ex. EnvelopeBuilder(xyInfo=updatedSpec[q]), EnvelopeBuilder(zInfo=updatedZspec[q])
        '''
        self.QsXyInfo = xyInfo
        self.QszInfo = zInfo
    
    def build_XYwaveform(self,axis:str,**kwargs)->dict:
        ''' Create the pulse waveform for XY control for target qubit\n
            func: "drag" or "gauss"\n
            axis: "x" or "y" or "x/2" or "y/2" or "-x/2" or "-y/2"\n
            kwargs: "sfactor" for pi-pulse sigma,\n
            "given_wf_array"(** not done!) a dict contains key "I" and "Q" for the given array waveform (arbitrary),\n
            ex. given_wf_array = {"I":array([0.1,0.1,0.1]),"Q":array([0.1,0.8,0.1])}
        '''
        from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms, drag_cosine_pulse_waveforms
        from exp.customized_waveform_tools import multi_sine_pulse_waveforms

        # search the waveform function
        
        func = 'drag' if self.QsXyInfo["waveform_func"] == 0 else self.QsXyInfo["waveform_func"] 
        if func.lower() in ['drag','dragg','gdrag']:
            def wf_func(amp, width, sigma, *args):
                return drag_gaussian_pulse_waveforms(amp, width, sigma, args[0], args[1], args[2])
        elif func.lower() in ['gauss','g','gaussian']:
            def wf_func(amp, width, sigma, *args):
                return drag_gaussian_pulse_waveforms(amp, width, sigma, 0, args[1], args[2])
        elif func.lower() in ['sin','sine']:
            def wf_func(amp, width, *args):
                return multi_sine_pulse_waveforms(amp, width, args[1], args[2])
        else:
            raise ValueError("Only surpport Gaussian or DRAG-gaussian waveform!")
        
        # Create the waveform array for I and Q
        angle = axis.split("/")[-1] # if "X/2" angle = 2, other angle = 'x'...
        rota_direction = -1 if axis.split("/")[0][0]=="-" else 1

        if angle in ["2"]:
            correspond_name = str(int(180/int(angle)))
            # check the /2 modified scale in the spec
            if correspond_name in list(self.QsXyInfo["pi_ampScale"].keys()):
                scale_90 = self.QsXyInfo["pi_ampScale"][correspond_name]
            else:
                scale_90 = 1
            scale = rota_direction*0.5*scale_90
        else:
            scale = rota_direction*1

        # check pulse sigma
        if kwargs != {} and "sfactor" in list(kwargs.keys()):
            S_factor = kwargs["sfactor"]
        else:
            S_factor = 4

        if kwargs != {} and "given_wf_array" in list(kwargs.keys()):
            use_given_wf = True
            if "I" in list(kwargs["given_wf_array"].keys()) and "Q" in list(kwargs["given_wf_array"].keys()):
                given_wf = kwargs["given_wf_array"]
            else:
                raise ValueError(f"The keynames in given_wf_array dict should be 'I' and 'Q', but recieved keynames: {kwargs['given_wf_array'].keys()}")
        else :
            use_given_wf = False

        if 'x' in axis[:2].lower():
            wf, der_wf = array(
                wf_func(self.QsXyInfo["pi_amp"]*scale, self.QsXyInfo["pi_len"], self.QsXyInfo["pi_len"]/S_factor, self.QsXyInfo["drag_coef"], self.QsXyInfo["anharmonicity"], self.QsXyInfo["AC_stark_detuning"])
            )
            I_wf = wf
            Q_wf = der_wf
        elif 'y' in axis[:2].lower():
            wf, der_wf = array(
                wf_func(self.QsXyInfo["pi_amp"]*scale, self.QsXyInfo["pi_len"], self.QsXyInfo["pi_len"]/S_factor, self.QsXyInfo["drag_coef"], self.QsXyInfo["anharmonicity"], self.QsXyInfo["AC_stark_detuning"])
            )
            I_wf = (-1)*der_wf
            Q_wf = wf 
        elif 'multisin' in axis[:].lower():
            wf, der_wf = array(
                wf_func(self.QsXyInfo["pi_amp"]*scale, self.QsXyInfo["pi_len"], self.QsXyInfo["anharmonicity"], self.QsXyInfo["AC_stark_detuning"])
            )
            I_wf = wf
            Q_wf = der_wf
        else:
            print(axis[0].lower())
            raise ValueError("Check the given axis, It should start with 'x' or 'y'!")
    
        if use_given_wf:
            return given_wf
        else:
            return {"I":I_wf, "Q":Q_wf}
        
    def build_zWaveform(self,axis:str,**kwargs)->dict:
        ''' Create the pulse waveform for XY control for target qubit\n
            func: "sin"\n
            "given_wf_array"(** not done!) a dict contains key "manual" for the given array waveform (arbitrary),\n
            ex. given_wf_array = {"manual":array([0.1,0.1,0.1])}
        '''
        from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms, drag_cosine_pulse_waveforms
        from exp.customized_waveform_tools import z_sine_pulse_waveforms

        # search the waveform function
        func = 'sin' if self.QszInfo["waveform_func"] == 0 else self.QszInfo["waveform_func"]
        if func.lower() in ['sin','sine']:
            def wf_func(amp, width, *args):
                return z_sine_pulse_waveforms(amp, width, args[0], args[1])
        else:
            raise ValueError("Only surpport sine waveform!")

        if kwargs != {} and "given_wf_array" in list(kwargs.keys()):
            if "manual" in list(kwargs["given_wf_array"].keys()):
                given_wf = kwargs["given_wf_array"]
                return given_wf
            else:
                raise ValueError(f"The keynames in given_wf_array dict should be 'wf', but recieved keynames: {kwargs['given_wf_array'].keys()}")
        elif 'sin' in axis[:].lower():  
            wf = array(
                wf_func(self.QszInfo["z_amp"], self.QszInfo["z_len"], self.QszInfo["z_freq"], self.QszInfo["z_phase"])
            )
        else:
            print(axis[0].lower())
            raise ValueError("Check the given axis, It should start with 'sin'!")
        
        return wf