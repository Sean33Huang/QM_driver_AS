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
        from exp.customized_waveform_tools import drag_multi_sine_pulse_waveforms, double_multi_sine_pulse_waveforms

        # search the waveform function
        
        func = 'dragg' if self.QsXyInfo["waveform_func"] == 0 else list(self.QsXyInfo["waveform_func"].keys())[0]
        if func.lower() in ['dragg','gdrag']:
            sfactor = 4
            if self.QsXyInfo["waveform_func"] != 0:
                if 'dragg' in self.QsXyInfo["waveform_func"].keys() and 'sfactor' in self.QsXyInfo["waveform_func"]['dragg'].keys():
                    sfactor = self.QsXyInfo["waveform_func"]['dragg']['sfactor'] 
            func_param = [self.QsXyInfo["pi_len"]/sfactor]
            def wf_func(amp, width, draga, anh, ac, *args):
                return drag_gaussian_pulse_waveforms(amplitude=amp, 
                                                     length=width, 
                                                     alpha=draga, 
                                                     anharmonicity=anh,
                                                     detuning=ac,
                                                     sigma=args[0])
        elif func.lower() in ['gauss','g','gaussian']:
            sfactor = 4
            if 'gauss' in self.QsXyInfo["waveform_func"].keys() and 'sfactor' in self.QsXyInfo["waveform_func"]['dragg'].keys():
                sfactor = self.QsXyInfo["waveform_func"]['dragg']['sfactor'] 
            func_param = [self.QsXyInfo["pi_len"]/sfactor]
            def wf_func(amp, width, draga, anh, ac, *args):
                return drag_gaussian_pulse_waveforms(amplitude=amp, 
                                                     length=width, 
                                                     alpha=0, 
                                                     anharmonicity=anh,
                                                     detuning=ac,
                                                     sigma=args[0])
        elif func.lower() in ['double_multisin']:
            func_param = [self.QsXyInfo["waveform_func"]['double_multisin']['wx2_amp'],
                          self.QsXyInfo["waveform_func"]['double_multisin']['wx3_amp']
                          ]
            def wf_func(amp, width, draga, anh, ac, *args):
                return double_multi_sine_pulse_waveforms(amplitude=amp, 
                                                         length=width, 
                                                         alpha=draga, 
                                                         anharmonicity=anh,
                                                         detuning=ac,
                                                         wx2_amp=args[0],
                                                         wx3_amp=args[1])
        elif func.lower() in ['drag_multisin']:
            func_param = [self.QsXyInfo["waveform_func"]['drag_multisin']['wx2_amp'],
                          self.QsXyInfo["waveform_func"]['drag_multisin']['wx3_amp']
                          ]
            def wf_func(amp, width, draga, anh, ac, *args):
                return drag_multi_sine_pulse_waveforms(amplitude=amp, 
                                                       length=width, 
                                                       alpha=draga, 
                                                       anharmonicity=anh,
                                                       detuning=ac,
                                                       wx2_amp=args[0],
                                                       wx3_amp=args[1])
        else:
            raise ValueError("Only surpport Gaussian or DRAG-gaussian waveform!")
        
        # Create the waveform array for I and Q
        angle = axis.split("/")[-1] # if "X/2" angle = 2, other angle = 'x'...
        rota_direction = -1 if axis.split("/")[0][0]=="-" else 1

        # Manual waveform
        if kwargs != {} and "given_wf_array" in list(kwargs.keys()):
            if "I" in list(kwargs["given_wf_array"].keys()) and "Q" in list(kwargs["given_wf_array"].keys()):
                given_wf = kwargs["given_wf_array"]
                return given_wf
            else:
                raise ValueError(f"The keynames in given_wf_array dict should be 'I' and 'Q', but recieved keynames: {kwargs['given_wf_array'].keys()}")

        # Defult waveform
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

        if 'x' in axis[:2].lower():
            wf, der_wf = array(
                wf_func(self.QsXyInfo["pi_amp"]*scale, 
                        self.QsXyInfo["pi_len"], 
                        self.QsXyInfo["drag_coef"], 
                        self.QsXyInfo["anharmonicity"], 
                        self.QsXyInfo["AC_stark_detuning"],
                        *func_param)
            )
            I_wf = wf
            Q_wf = der_wf
        elif 'y' in axis[:2].lower():
            wf, der_wf = array(
                wf_func(self.QsXyInfo["pi_amp"]*scale, 
                        self.QsXyInfo["pi_len"], 
                        self.QsXyInfo["drag_coef"], 
                        self.QsXyInfo["anharmonicity"], 
                        self.QsXyInfo["AC_stark_detuning"],
                        *func_param)
            )
            I_wf = (-1)*der_wf
            Q_wf = wf 
        else:
            print(axis[0].lower())
            raise ValueError("Check the given axis, It should start with 'x' or 'y'!")
               
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