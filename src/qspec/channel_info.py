from numpy import array, cos, sin, pi, arange
from qm.octave import QmOctaveConfig
from qm.QuantumMachinesManager import QuantumMachinesManager
from QM_driver_AS.ultitly.set_octave import OctaveUnit, octave_declaration

#######################
# AUXILIARY FUNCTIONS #
#######################
from qualang_tools.units import unit
u = unit(coerce_to_integer=True)


class ChannelInfo:
    """This object contains the information about RO and XY control on the chip"""
    def __init__(self,q_num=None,**kwargs):
        self.q_num = q_num
        if q_num != None:
            self.init_xyInfo()
            self.init_roInfo()
            self.init_zInfo()
            self.init_decoInfo()
            self.init_wireInfo()
            self.init_hardwareInfo()
        else:
            self._XyInfo = {}
            self._DecoInfo = {}
            self._ZInfo = {}
            self._WireInfo = {}
            self._RoInfo = {}
            self.init_hardwareInfo()

    # for hardware infomation
    def init_hardwareInfo(self):
        self._HardwareInfo = {}
        self._HardwareInfo["qop_ip"] = ""
        self._HardwareInfo["qop_port"] = None
        self._HardwareInfo["octave"] = {}
        self._HardwareInfo["cluster_name"] = ''
        self._HardwareInfo["controller_name"] = ("","")
        self._HardwareInfo["port_mapping"] = {}
        self._HardwareInfo["clock"] = ""

    def update_HardwareInfo(self,**kwargs):
        """
            Update the hardware information for this chip.\n
            **kwargs are the following:\n
            ip(qop_ip):str, qop_port: for QMmanager, cluster_name:str="QPX_2",
            ctrl_name:tuple=("octave1","con1")
        """
        if not hasattr(self,'_HardwareInfo'):
            self.init_hardwareInfo()
        if kwargs != {}:
            for info in list(kwargs.keys()):
                if info.lower() in ['ip', 'qop_ip']:
                    self._HardwareInfo["qop_ip"] = kwargs[info]
                elif info.lower() in ["qop_port"]:
                    self._HardwareInfo["qop_port"] = kwargs[info]
                elif info.lower() in ["cluster_name"]:
                    self._HardwareInfo["cluster_name"] = kwargs[info]
                else:
                    raise KeyError(f"Can't recognize the key with name='{info}'")
    def update_octave( self, name, **kwargs):
        """
        ip: ip of cluster in LAN.\n
        port:11XXX, XXX is last section of ip in cluster subnet.\n
        clock: "Internal", "External_10MHz", "External_100MHz" or "External_1000MHz".\n
        con: controller name in cluster.\n
        port_map:dict\n
        """
        if not hasattr(self,'_HardwareInfo'):
            self.init_hardwareInfo()
        # octave_info = {}
        octave_info = {"name":name}
        if kwargs != {}:
            for info in list(kwargs.keys()):
                match info:
                    case 'ip':
                        octave_info["ip"] = kwargs[info]
                    case "clock":
                        octave_info["clock"] = kwargs[info]
                    case "port":
                        octave_info["port"] = kwargs[info]
                    case "con":
                        octave_info["con"] = kwargs[info]
                    case "port_map":
                        octave_info["port_mapping"] = kwargs[info]
                    case _:
                        raise KeyError(f"Can't recognize the key with name='{info}'")
        self._HardwareInfo["octave"][name]=octave_info
        # print(self._HardwareInfo["octave"])

    def buildup_qmm(self):
        '''
            Build up the QuantumMachinesManager by the HardwareInfo.\n
            return QuantumMachinesManager -> for program executing, [OctaveUnit]-> for octave calibration
        '''
        # print(self._HardwareInfo["octave"])
        octaves = []
        for n, info in self._HardwareInfo["octave"].items():
            # Add the octaves
            octaves.append( OctaveUnit( n, self._HardwareInfo["qop_ip"], port=info["port"], con=info["con"], clock=info["clock"], port_mapping=info["port_mapping"]) )
        # Configure the Octaves
        octave_config = octave_declaration(octaves)
        qmm = QuantumMachinesManager(host=self._HardwareInfo["qop_ip"], port=self._HardwareInfo["qop_port"], cluster_name=self._HardwareInfo["cluster_name"], octave=octave_config)
        
        return qmm, octaves

    ### Below about RO information ###
    def init_roInfo(self):
        '''
            ## catagorized with qlabel, start from 1.
            keys in self.RoInfo: "resonator_LO_q1","resonator_IF_q2","readout_amp_q3","ge_threshold_q4",\n
            "RO_weights_q5","readout_len","time_of_flight","register".\n
            ### *** readout_len and time_of_flight are the same for all the qubits ***
        '''
        self._RoInfo = {}
        self._RoInfo["registered"] = []
        self._RoInfo["depletion_time"] = 1 * u.us
        dIF = 200/self.q_num
        init_IF = arange(-200,210,dIF)
        for idx in range(self.q_num):
            self._RoInfo[f"q{idx}"] = {}
            self._RoInfo[f"q{idx}"]["readout_len"] = 1500
            self._RoInfo[f"q{idx}"]["time_of_flight"] = 280
            for info in ['resonator_LO','resonator_IF','readout_amp','ge_threshold']:
                match info:
                    case 'resonator_LO':
                        init_value = 6 * u.GHz
                    case 'resonator_IF':
                        init_value = init_IF[idx] * u.MHz
                    case 'readout_amp':
                        init_value = 0.2 
                    case _:
                        init_value = 0.0
                self._RoInfo[f"q{idx}"][info] = init_value
            self._RoInfo[f"q{idx}"][f"RO_weights"]={}
            # RO weights paras includes default, rotated and optimal for a qubit
            
            for weights_cata in ["origin","rotated","optimal"]:
                # optimal for ex, save the computed dict for config to directly replace with it.
                if weights_cata != "optimal":
                    self._RoInfo[f"q{idx}"][f"RO_weights"][weights_cata] = (0/180)*pi

                # rotated for ex, save the rotated angle for confog to compute the exact value
                else:
                    self._RoInfo[f"q{idx}"][f"RO_weights"][weights_cata] = {}
        
            self._RoInfo["registered"].append(f"q{idx}")


    
    def give_depletion_time_for(self,target_r:str='all'):
        """
            return the paras for `initializer()` when its mode is 'depletion'.\n
            target_r: "q2" (will trnsform it to resonators automatically)
        """ 
        rrs = [] 
        if target_r.lower() == 'all':
            for q_idx in self._RoInfo["registered"]:
                rrs.append(f"{q_idx}_ro")
        else:
            rrs.append(f"{target_r}_ro")
        
        return (self._RoInfo["depletion_time"],rrs)



    def optimal_ROweights_generator(self, npz_file_path:str):
        from qualang_tools.config.integration_weights_tools import convert_integration_weights
        from numpy import load
        weights = load(npz_file_path)
        real = convert_integration_weights(weights["weights_real"])
        minus_imag = convert_integration_weights(weights["weights_minus_imag"])
        imag = convert_integration_weights(weights["weights_imag"])
        minus_real = convert_integration_weights(weights["weights_minus_real"])

        cosine_weight = {"cosine":real,"sine":minus_imag}
        sine_weight = {"cosine":imag,"sine":real}
        minus_sine_weight = {"cosine":minus_imag,"sine":minus_real}

        return {"cos":cosine_weight,"sin":sine_weight,"minus_sin":minus_sine_weight}
        

    def update_RoInfo_for(self, target_q:str, **kwargs):
        """
            target_q: "q4"\n
            kwargs: LO=6, IF=150, amp=0.08, len=2000, time(time_of_flight)= 280, ge_hold(ge_threshold)=0.05, depletion(depletion_time)= 700, offset=0 in ns 
            origin(ROweights) and rotated(ROweights) = (40/180)*pi, optimal(ROweights) = from `self.optimal_ROweights_generator()`.\n
            ### *** time_of_flight and len are shared with each qubits. *** 
        """
        few_freq = {}
        if kwargs != {}:
            for info in kwargs:
                match info.lower():
                    case "if":
                        self._RoInfo[target_q][f'resonator_IF'] = int(kwargs[info]*u.MHz)
                        few_freq[f'resonator_IF_{target_q}'] = int(kwargs[info]*u.MHz)
                    case "amp":
                        self._RoInfo[target_q][f'readout_amp'] = kwargs[info]
                    case "lo":
                        self._RoInfo[target_q][f'resonator_LO'] = int(kwargs[info]*u.GHz)
                        few_freq[f'resonator_LO_{target_q}'] = int(kwargs[info]*u.GHz)
                    case "len":
                        self._RoInfo[target_q]['readout_len'] = kwargs[info]
                    case "time":
                        self._RoInfo[target_q]['time_of_flight'] = kwargs[info]
                    case "depletion":
                        self._RoInfo[target_q]["depletion_time"] = int(kwargs[info]*u.ns)
                    case "ge_hold":
                        self._RoInfo[target_q][f'ge_threshold'] = kwargs[info]
                    case "origin":
                        self._RoInfo[target_q][f"RO_weights"]["origin"] = kwargs[info]
                    case "rotated":
                        self._RoInfo[target_q]["rotated"] = kwargs[info]
                    case "optimal":
                        self._RoInfo[target_q][f"RO_weights"]["optimal"] = kwargs[info]    
                    case "offset":
                        self._RoInfo[target_q]["offset"] = kwargs[info]  
                    case _:
                        raise KeyError("kwargs key goes wrong!")
        else:
            raise ValueError("You should give the info want to update!")
        return few_freq
    ### Below about XY information ###    
    def init_xyInfo(self):
        '''Info for a pi-pulse should envolve:\n
        1)pi_amp, 2)pi_len, 3)qubit_LO(GHz), 4)qubit_IF(MHz), 5)drag_coef, 6)anharmonicity(MHz), 7)AC_stark_detuning(MHz)
        '''
        self._XyInfo = {}
        self._XyInfo["register"] = []
        for idx in range(self.q_num):
            self._XyInfo[f'q{idx}'] = {}
            for info in ["pi_amp","pi_len","qubit_LO","qubit_IF","drag_coef","anharmonicity","AC_stark_detuning","waveform_func","pi_ampScale"]:
                match info :
                    case 'pi_amp':
                        init_value = 0.1
                    case 'pi_len':
                        init_value = 40
                    case 'qubit_LO':
                        init_value = 4 * u.GHz
                    case 'qubit_IF':
                        init_value = -100 * u.MHz
                    case 'drag_coef':
                        init_value = 0.5
                    case 'anharmonicity':
                        init_value = -200 * u.MHz
                    case "AC_stark_detuning":
                        init_value = 0 * u.MHz
                    case "waveform_func":
                        init_value = 'drag'
                    case _:
                        init_value = {"180":1,"90":1}
                self._XyInfo[f'q{idx}'][info] = init_value 
            self._XyInfo["register"].append(f"q{idx}")
        # CW pulse info
            self._XyInfo[f'q{idx}']["const_len"] = 10 * u.us
            self._XyInfo[f'q{idx}']["const_amp"] = 0.5
        # Saturation pulse info
        self._XyInfo["saturation_len"] = 5 * u.us
        self._XyInfo["saturation_amp"] = 0.1
        
    def update_aXyInfo_for(self,target_q,**kwargs):
        '''target_q : "q5"\n
        kwargs :\n
        amp(pi_amp)=0.2,\n 
        len(pi_len)=20,\n 
        LO(qubit_LO, GHz)=4.3,\n
        IF(qubit_IF, MHz)=80,\n
        draga(drag_coef)=0.5,\n
        delta or anh or d(anharmonicity, MHz)=-200,\n
        AC(AC_stark_detuning, MHz)=8,func='gauss' or 'drag',\n
        half_scale or half(half_pi_ampScale)=0.012.\n
        const_amp default 0.5\n
        ### If update info is related to freq return the dict for updating the config.
        '''
        new_freq = {}
        for name in list(kwargs.keys()):
            if name.lower() == 'amp':
                self._XyInfo[target_q]["pi_amp"] = kwargs[name] 
            elif name.lower() == 'len':
                self._XyInfo[target_q]["pi_len"] = kwargs[name]
            elif name.lower() == 'lo':
                self._XyInfo[target_q]["qubit_LO"] = int(kwargs[name]*u.GHz)
                new_freq["qubit_LO_"+target_q] = int(kwargs[name]*u.GHz)
            elif name.lower() == 'if':
                self._XyInfo[target_q]["qubit_IF"] = int(kwargs[name]*u.MHz)
                new_freq["qubit_IF_"+target_q] = int(kwargs[name]*u.MHz)
            elif name.lower() in ['draga','drag_coef'] :
                self._XyInfo[target_q]["drag_coef"] = kwargs[name]
            elif name.lower() in ["delta","d","anh","anharmonicity"]:
                self._XyInfo[target_q]["anharmonicity"] = int(kwargs[name]*u.MHz)
            elif name.lower() in ['ac',"AC_stark_detuning"]:
                self._XyInfo[target_q]["AC_stark_detuning"] = int(kwargs[name]*u.MHz)
            elif name.lower() in ['waveform',"func",'wf']:
                self._XyInfo[target_q]["waveform_func"] = kwargs[name]
            elif name.lower() in ['half_scale','half']:
                self._XyInfo[target_q]["pi_ampScale"]["90"] = kwargs[name]
            elif name.lower() in ['const_amp']:
                self._XyInfo[target_q]["const_amp"] = kwargs[name]
            else:
                print(name.lower())
                raise KeyError("I don't know what you are talking about!")
        print(new_freq)
        return new_freq
    
    def export_spec( self, path ):
        import pickle
        # define dictionary
        # create a binary pickle file 
        f = open(path,"wb")
        # write the python object (dict) to pickle file
        spec = {"RoInfo":self._RoInfo,"XyInfo":self._XyInfo,"ZInfo":self._ZInfo,"DecoInfo":self._DecoInfo,"WireInfo":self._WireInfo, "HardwareInfo":self._HardwareInfo}
        pickle.dump(spec,f)
        # close file
        f.close()
    




    ### Below about decoherence time T1 and T2
    def init_decoInfo(self):
        """
            DecoInfo will be like : {"q1":{"T1":10000000,"T2":20000000},"q2":....}
        """
        self._DecoInfo = {}
        for idx in range(self.q_num):
            self._DecoInfo[f"q{idx}"] = {"T1":0,"T2":0,"T2e":0,"T2s":0}

    def update_DecoInfo_for(self,target_q:str,**kwargs):
        '''
            update the decoherence info for target qubit like T1 and T2.\n
            target_q : "q1"\n
            kwargs : "T1"= us, "T2"= us, "T2e"=us,  "T2s"(T2*)=us one of them or all are surpported.
        '''
        if kwargs != {}:
            for info in kwargs:
                if info.lower() in ["t1","t2","t2e","t2s"]:
                   self._DecoInfo[target_q][info.upper()] = kwargs[info] * u.us  
                else:
                    raise KeyError("Only two types are surpported: T1 and T2!")
        else:
            raise ValueError("You should give the info want to update in kwargs!")
        
    ### Below about the z offset info
    def init_zInfo(self):
        """
            initialize Zinfo with: {"q1":{"controller":"con1","con_channel":1,"offset":0.0,"OFFbias":0.0,"idle":0.0},"q2":....}
        """
        self._ZInfo = {}
        for idx in range(self.q_num):
            self._ZInfo[f"q{idx}"] = {
                "offset":0.0,
                "OFFbias":0.0,
                "idle":0.0,
                "crosstalk":{},
                "z_len" : 600,
                "z_amp" : 0.5,
                "z_freq" : 1,
                "z_phase" : 0,
                "waveform_func" : "sin"
            }

        self._ZInfo["settle_time"] = 500 * u.ns

    def update_ZInfo_for(self,target_q:str,**kwargs):
        """
            Update the z info for target qubit: ctrler channel, offset, OFFbias and idle encluded.\n
            target_q: "q3"...\n
            kwargs: controller='con2', con_channel=2, offset=0.03, OFFbias=-0.2, idle=-0.1, settle=400(in ns), len(const_flux_len)=500\n
            return the target_q's z info for config.
        """
        if kwargs != {}:
            for info in kwargs:
                if info.lower() in ["controller","con_channel","offset","offbias","idle"]:
                    self._ZInfo[target_q][info] = kwargs[info]
                elif info.lower() in ["crosstalk"]:
                    self._ZInfo[target_q][info] = kwargs[info]
                elif info.lower() in ["settle"]:
                    self._ZInfo["settle_time"] = int(kwargs[info]*u.ns)
                elif info.lower() in ["len","amp","freq","phase"]:
                    self._ZInfo[target_q][f"z_{info.lower()}"] = kwargs[info]
                elif info.lower() in ['waveform',"func",'wf']:
                    self._ZInfo[target_q]["waveform_func"] = kwargs[info]
                else:
                    raise KeyError("Some variables can't be identified, check the kwargs!")
        else:
            print(f"Return the Zinfo about {target_q}")
        return self._ZInfo[target_q]

    ### physical wiring info
    def init_wireInfo(self):
        self._WireInfo = {}
        for idx in range(self.q_num):
            self._WireInfo[f"q{idx}"] = {
                "ro_mixer":f'octave1_ro', 
                "xy_mixer":f'octave1_q{idx}',
                "rin_I":('con1',1),
                "rin_Q":('con1',2),
                "rout_I":('con1',1),
                "rout_Q":('con1',2),
                "xy_I":('con1',3),
                "xy_Q":('con1',4),
                "z":('con1',5)
                }
         
    
    def update_WireInfo_for(self, target_q:str ,**kwargs):
        """
            target_q: "q3".\n
            kwargs: 
                "ro_mixer":f'octave1_ro',\n
                "xy_mixer":f'octave1_q{idx}', \n
                "rin_I":('con1',1),\n
                "rin_Q":('con1',2),\n
                "rout_I":('con1',1),\n
                "rout_Q":('con1',2),\n
                "xy_I":('con1',3),\n
                "xy_Q":('con1',4),\n
                "z":('con1',5)\n
                
        """
        if kwargs != {}:
            for info in kwargs:
                print(kwargs)
                if info in ['ro_mixer','xy_mixer','rin_I','rin_Q','rout_I','rout_Q','xy_I','xy_Q', 'z']:
                    self._WireInfo[target_q][info] = kwargs[info]
                else:
                    raise KeyError("Check the wiring info key plz!")
        else:
            raise ValueError("You should give the info want to update!")
        
    def get_ReadableSpec_fromQ(self, target_q:str, specific:str='all'):
        """
            ### Get the spec for target_q includes WireInfo, ZInfo, DecoInfo, RoInfo and XyInfo.\n
            target_q: "q3",\n
            specific: get the specific info, default for all.\n
            'wire' for WireInfo,\n
            'z' for ZInfo,\n
            'deco' for DecoInfo,\n
            'ro' for RoInfo,\n
            'xy' for XyInfo.
        """
        match specific.lower():
            case 'wire':
                want_item = {'WireInfo':self._WireInfo}
            case 'z':
                want_item = {'ZInfo':self._ZInfo}
            case 'deco':
                want_item = {'DecoInfo':self._DecoInfo}
            case 'ro':
                want_item = {'RoInfo':self._RoInfo}
            case 'xy':
                want_item = {'XyInfo':self._XyInfo}
            case _:
                want_item = {'XyInfo':self._XyInfo,'DecoInfo':self._DecoInfo,'RoInfo':self._RoInfo,'ZInfo':self._ZInfo,'WireInfo':self._WireInfo}
        
        request_item = {}
        for info_name in list(want_item.keys()):
            request_item[info_name] = want_item[info_name][target_q]

        return request_item
    
    def get_spec_forConfig(self,whichSpec:str):
        """
            return the spec for dynamic configuration maintenance.\n
            whichSpec: \n
            'wire' for WireInfo,\n
            'z' for ZInfo,\n
            'deco' for DecoInfo,\n
            'ro' for RoInfo,\n
            'xy' for XyInfo.
        """
        from copy import deepcopy
        match whichSpec.lower():
            case 'xy':
                return deepcopy(self._XyInfo)
            case 'ro':
                return deepcopy(self._RoInfo)
            case 'z':
                return deepcopy(self._ZInfo)
            case 'deco':
                return deepcopy(self._DecoInfo)
            case 'wire':
                return deepcopy(self._WireInfo)
            case _:
                raise KeyError(f"I don't know which info you need with the given info name: {whichSpec}")

    def give_WaitTime_with_q(self,target_q:str='all',wait_scale:float=5):
        '''
            return the T1 based on the given target_q multiplied the waiting scale: scale*T1\n
            target_q: "q3",\n
            wait_scale: 5.5
        '''
        if target_q=='all':
            qs = list(self._DecoInfo.keys())
            if len(qs)>0:
                T1s = []
                for q in qs:
                    T1s.append(self._DecoInfo[q]["T1"])
                from numpy import array, max
                target_T1 = max(array(T1s)) 
            else:
                wait_scale = 1
                target_T1 = 100 * u.us
        else:
            try:
                target_T1 = float(self._DecoInfo[target_q]["T1"])  
                if target_T1 == 0:
                    print(f"the decoherence info haven't been registered by {target_q}, i'll give u 100 us!")
                    target_T1 = 100 * u.us
                    wait_scale = 1
                
            except:
                print(f"the decoherence info haven't been registered by {target_q}, i'll give u 100 us!")
                target_T1 = 100 * u.us
                wait_scale = 1
        return int(wait_scale*target_T1)

    def get_HardwareInfo(self):
        return self._HardwareInfo

def import_spec( path )->ChannelInfo:
    import pickle
    # Read dictionary pkl file
    with open(path, 'rb') as fp:
        spec = pickle.load(fp)
    import_ChannelInfo = ChannelInfo()
    import_ChannelInfo._XyInfo = spec["XyInfo"]
    import_ChannelInfo._DecoInfo = spec["DecoInfo"]
    import_ChannelInfo._ZInfo = spec["ZInfo"]
    import_ChannelInfo._WireInfo = spec["WireInfo"]
    import_ChannelInfo._RoInfo = spec["RoInfo"]
    import_ChannelInfo._HardwareInfo = spec["HardwareInfo"]
    print("import_spec information loaded successfully!")

    return import_ChannelInfo
