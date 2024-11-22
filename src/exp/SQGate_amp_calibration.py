from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qualang_tools.loops import from_array
import exp.config_par as gc

from exp.RO_macros import multiRO_declare, multiRO_measurement, multiRO_pre_save

import warnings
warnings.filterwarnings("ignore")

from qualang_tools.units import unit
u = unit(coerce_to_integer=True)

from exp.QMMeasurement import QMMeasurement

import xarray as xr

class SQGate_amp_calibration( QMMeasurement ):

    def __init__( self, config, qmm: QuantumMachinesManager ):
        super().__init__( config, qmm )
        self.ro_elements = ['q4_ro']
        self.xy_elements = ['q4_xy']
        self.amp_ratio = 1
        self.sequence_repeat = 1
        self.freq_range = ( -1, 1 )
        self.freq_resolution = 0.5

        self.initializer = None
        self.process = "amp" # 'amp' or 'repeat'or 'freq'
        self.gate = 1
        # 1 = X X
        # 2 = X -X
        # 3 = Y Y
        # 4 = Y -Y
        # 11 = X/2 X/2 X/2 X/2

    def _get_qua_program(self):

        amp_modify_range = 0.4/float(self.sequence_repeat)
        a_min = 1-amp_modify_range
        a_max = 1+amp_modify_range
        da = amp_modify_range/50
        self.amp_ratios = np.arange(a_min, a_max + da / 2, da)  # + da/2 to add a_max to amplitudes
        amp_len = len(self.amp_ratios)

        self.qua_freqs = self._lin_freq_array()
        freq_len = len(self.qua_freqs)
        self._attribute_config()

        match self.process:
            case 'amp':
                with program() as qua_prog:
                    n = declare(int)  # QUA variable for the averaging loop
                    a = declare(fixed)  # QUA variable for the DRAG coefficient pre-factor
                    iqdata_stream = multiRO_declare( self.ro_elements )
                    n_st = declare_stream()  # Stream for the averaging iteration 'n'
                    
                    with for_(n, 0, n < self.shot_num, n + 1):
                        with for_(*from_array(a, self.amp_ratios)):
                            # Init
                            if self.initializer is None:
                                # wait(thermalization_time * u.ns)
                                wait(100 * u.us)
                            else:
                                try:
                                    self.initializer[0](*self.initializer[1])
                                except:
                                    print("Initializer didn't work!")
                                    wait(100*u.us)
                            for _ in range(self.sequence_repeat):
                                for xy in self.xy_elements:
                                    self._play_sequence(a, xy)
                            
                                # Operation
                                # with switch_(r_idx, unsafe=True):
                                #     with case_(0):
                                #         for _ in range(n_90):
                                #             play("x90" * self.amp_ratios(a), self.xy_elements[0])
                                #     with case_(1):
                                #         for _ in range(n_pi):
                                #             play("x180" * self.amp_ratios(a), self.xy_elements[0])

                                # Align after playing the qubit pulses.
                            align()
                                # Readout
                            multiRO_measurement(iqdata_stream, self.ro_elements, weights="rotated_")         
                            
                        save(n, n_st)
                    with stream_processing():
                        # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
                        multiRO_pre_save(iqdata_stream, self.ro_elements, (amp_len,))
                        n_st.save("iteration")

            case 'repeat':
                with program() as qua_prog:
                    n = declare(int)  # QUA variable for the averaging loop
                    rep = declare(int)  # QUA variable for the measured 'repeat' quadrature
                    iqdata_stream = multiRO_declare( self.ro_elements )
                    n_st = declare_stream()  # Stream for the averaging iteration 'n'
                    
                    a = declare(fixed)  
                    assign(a, 1)

                    with for_(n, 0, n < self.shot_num, n + 1):
                        with for_(rep, 1, rep <= self.sequence_repeat, rep + 1):
                            # Init
                            if self.initializer is None:
                                # wait(thermalization_time * u.ns)
                                wait(100 * u.us)
                            else:
                                try:
                                    self.initializer[0](*self.initializer[1])
                                except:
                                    print("Initializer didn't work!")
                                    wait(100*u.us)

                            for xy in self.xy_elements:
                                i = declare(int)
                                with for_(i, 0, i < rep, i + 1):
                                    self._play_sequence(a, xy)
                            # Operation
                            # with switch_(r_idx, unsafe=True):
                            #     with case_(0):
                            #         for _ in range(n_90):
                            #             play("x90" * self.amp_ratios(a), self.xy_elements[0])
                            #     with case_(1):
                            #         for _ in range(n_pi):
                            #             play("x180" * self.amp_ratios(a), self.xy_elements[0])

                            # Align after playing the qubit pulses.
                            align()
                            # Readout
                            multiRO_measurement(iqdata_stream, self.ro_elements, weights="rotated_")         
                            
                        save(n, n_st)
                    with stream_processing():
                        # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
                        multiRO_pre_save(iqdata_stream, self.ro_elements, (self.sequence_repeat,) )
                        n_st.save("iteration")

            # Not yet
            case 'freq':
                with program() as qua_prog:
                    n = declare(int)    # QUA variable for the averaging loop
                    df = declare(int)   # QUA variable for the frequencies
                    iqdata_stream = multiRO_declare( self.ro_elements )
                    n_st = declare_stream()  # Stream for the averaging iteration 'n'

                    a = declare(fixed)  
                    assign(a, 1)
                    
                    with for_(n, 0, n < self.shot_num, n + 1):
                        with for_(*from_array(df, self.qua_freqs)):
                            # Init
                            if self.initializer is None:
                                # wait(thermalization_time * u.ns)
                                wait(100 * u.us)
                            else:
                                try:
                                    self.initializer[0](*self.initializer[1])
                                except:
                                    print("Initializer didn't work!")
                                    wait(100*u.us)
                            for i, xy in enumerate(self.xy_elements):
                                update_frequency( xy, self.ref_xy_IF[i] +df )
                                self._play_sequence(a, xy)
                            # Operation
                            # with switch_(r_idx, unsafe=True):
                            #     with case_(0):
                            #         for _ in range(n_90):
                            #             play("x90" * self.amp_ratios(a), self.xy_elements[0])
                            #     with case_(1):
                            #         for _ in range(n_pi):
                            #             play("x180" * self.amp_ratios(a), self.xy_elements[0])

                            # Align after playing the qubit pulses.
                            align()
                            # Readout
                            multiRO_measurement(iqdata_stream, self.ro_elements, weights="rotated_")         
                            
                        save(n, n_st)
                    with stream_processing():
                        # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
                        multiRO_pre_save(iqdata_stream, self.ro_elements, (freq_len,))
                        n_st.save("iteration")
        
        return qua_prog
    
    def _get_fetch_data_list( self ):

        ro_ch_name = []
        for r_name in self.ro_elements:
            ro_ch_name.append(f"{r_name}_I")
            ro_ch_name.append(f"{r_name}_Q")
        data_list = ro_ch_name + ["iteration"]
        return data_list
    
    def _data_formation( self ):
        match self.process:
            case 'amp':
                param_name = "amplitude_ratio"
                param_val = self.amp_ratios
            case 'repeat':
                param_name = 'repeat_time'
                param_val = np.arange(0, self.sequence_repeat, 1)
            case 'freq':
                param_name = 'frequency'
                param_val = self.qua_freqs/1e6
        output_data = {}
        for r_idx, r_name in enumerate(self.ro_elements):
            output_data[r_name] = ( ["mixer",param_name],
                                np.array([self.fetch_data[r_idx*2], self.fetch_data[r_idx*2+1]]))
        dataset = xr.Dataset(
            output_data,
            coords={ "mixer":np.array(["I","Q"]) , param_name: param_val}
        )

        return dataset
    
    def _play_sequence(self, a, xy):
        r_idx = declare(int)  # QUA variable for the measured 'I' quadrature
        assign(r_idx, self.gate)

        with switch_(r_idx, unsafe=True):
            with case_(1):
                play("x180" * amp(a), xy)
                play("x180" * amp(a), xy)
            with case_(2):
                play("x180" * amp(a), xy)
                play("-x180" * amp(a), xy)  
            with case_(3):
                play("y180" * amp(a), xy)
                play("y180" * amp(a), xy)  
            with case_(4):
                play("y180" * amp(a), xy)
                play("-y180" * amp(a), xy)  

            with case_(11):
                play("x90" * amp(a), xy)
                play("x90" * amp(a), xy)
                play("x90" * amp(a), xy)
                play("x90" * amp(a), xy)

    def _gate_match(self):
        match self.gate:
            case 1:
                return 'X X'
            case 2:
                return 'X -X'
            case 3:
                return 'Y Y'
            case 4:
                return 'Y -Y'
            case 11:
                return 'X/2 X/2 X/2 X/2'
            
    def _lin_freq_array( self ):

        freq_r1_qua = self.freq_range[0] * u.MHz
        freq_r2_qua = self.freq_range[1] * u.MHz
        freq_resolution_qua = self.freq_resolution * u.MHz
        freqs_qua = np.arange(freq_r1_qua,freq_r2_qua,freq_resolution_qua )
        
        return freqs_qua
    
    def _attribute_config( self ):
        self.ref_ro_IF = []
        self.ref_ro_LO = []
        for r in self.ro_elements:
            self.ref_ro_IF.append(gc.get_IF(r, self.config))
            self.ref_ro_LO.append(gc.get_LO(r, self.config))

        self.ref_xy_IF = []
        self.ref_xy_LO = []
        for xy in self.xy_elements:
            self.ref_xy_IF.append(gc.get_IF(xy, self.config))
            self.ref_xy_LO.append(gc.get_LO(xy, self.config))
