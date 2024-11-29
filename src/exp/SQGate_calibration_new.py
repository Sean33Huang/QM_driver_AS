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

class SQGate_calibration( QMMeasurement ):

    def __init__( self, config, qmm: QuantumMachinesManager ):
        super().__init__( config, qmm )
        self.ro_elements = ['q4_ro']
        self.xy_elements = ['q4_xy']
        
        self.amp_ratio = 1
        self.sequence_repeat = 1
        
        self.virtial_detune_freq = 10
        self.point_per_period = 1
        self.max_period = 1
        
        self.draga_points = 40

        self.initializer = None
        self.process = "amp" # 'amp' or 'freq' or 'drag'

    def _get_qua_program(self):

        match self.process:
            
            case 'amp':
                amp_modify_range = 0.4/float(self.sequence_repeat)
                a_min = 1-amp_modify_range
                a_max = 1+amp_modify_range
                da = amp_modify_range/50
                self.amp_ratios = np.arange(a_min, a_max + da / 2, da)  # + da/2 to add a_max to amplitudes
                amp_len = len(self.amp_ratios)
                with program() as qua_prog:
                    n = declare(int)  # QUA variable for the averaging loop
                    a = declare(fixed)  # QUA variable for the DRAG coefficient pre-factor
                    r_idx = declare(int)  # QUA variable for the measured 'I' quadrature
                    iqdata_stream = multiRO_declare( self.ro_elements )
                    n_st = declare_stream()  # Stream for the averaging iteration 'n'
                    
                    with for_(n, 0, n < self.shot_num, n + 1):
                        with for_each_(r_idx, [0, 1]):
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
                                with switch_(r_idx, unsafe=True):
                                    with case_(0):
                                        for xy in self.xy_elements:
                                            for _ in range(self.sequence_repeat):
                                                play('x180' * amp(a), xy)
                                                play('x180' * amp(a), xy)
                                    with case_(1):
                                        for xy in self.xy_elements:
                                            for _ in range(self.sequence_repeat):
                                                play('x90' * amp(a), xy)
                                                play('x90' * amp(a), xy)
                                                play('x90' * amp(a), xy)
                                                play('x90' * amp(a), xy)
                                    # Align after playing the qubit pulses.
                                align()
                                    # Readout
                                multiRO_measurement(iqdata_stream, self.ro_elements, weights="rotated_")         
                            
                        save(n, n_st)
                    with stream_processing():
                        # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
                        multiRO_pre_save(iqdata_stream, self.ro_elements, (2, amp_len))
                        n_st.save("iteration")

            # not yet
            case 'freq':
                self.qua_cc_evo = self._lin_time_array()
                time_len = len(self.qua_cc_evo)
                self.time_ns = self.qua_cc_evo * 4
                with program() as qua_prog:
                    iqdata_stream = multiRO_declare( self.ro_elements )
                    n = declare(int)
                    n_st = declare_stream()
                    t = declare(int)  # QUA variable for the idle time
                    phi = declare(fixed)  # Phase to apply the virtual Z-rotation
                    phi_idx = declare(bool,)
                    with for_(n, 0, n < self.shot_num, n + 1):
                        with for_each_( phi_idx, [True, False]):
                            with for_(*from_array(t, self.qua_cc_evo)):

                                # Rotate the frame of the second x90 gate to implement a virtual Z-rotation
                                # 4*tau because tau was in clock cycles and 1e-9 because tau is ns
                                
                                # Init
                                if self.initializer is None:
                                    wait(100*u.us)
                                    #wait(thermalization_time * u.ns)
                                else:
                                    try:
                                        self.initializer[0](*self.initializer[1])
                                    except:
                                        print("Initializer didn't work!")
                                        wait(100*u.us)

                                # Operation
                                True_value = Cast.mul_fixed_by_int(self.virtial_detune_freq * 1e-3, 4 * t)
                                False_value = Cast.mul_fixed_by_int(-self.virtial_detune_freq * 1e-3, 4 * t)
                                assign(phi, Util.cond(phi_idx, True_value, False_value))

                                for q in self.xy_elements:
                                    play("x90", q)  # 1st x90 gate

                                for q in self.xy_elements:
                                    wait(t, q)

                                for q in self.xy_elements:
                                    frame_rotation_2pi(phi, q)  # Virtual Z-rotation
                                    play("x90", q)  # 2st x90 gate

                                # Align after playing the qubit pulses.
                                align()
                                # Readout
                                multiRO_measurement(iqdata_stream, self.ro_elements, weights="rotated_")         
                            

                        # Save the averaging iteration to get the progress bar
                        save(n, n_st)

                    with stream_processing():
                        n_st.save("iteration")
                        multiRO_pre_save(iqdata_stream, self.ro_elements, (2,time_len) )
                        
            case 'drag':
                a_min = 0
                a_max = 1.5
                draga_points = 40
                da = (a_max-a_min)/draga_points
                self.amps = np.arange(a_min, a_max + da, da)  # + da/2 to add a_max to amplitudes
                amp_len = len(self.amps)
                with program() as qua_prog:
                    n = declare(int)  # QUA variable for the averaging loop
                    a = declare(fixed)  # QUA variable for the DRAG coefficient pre-factor
                    op_idx = declare(int)
                    iqdata_stream = multiRO_declare( self.ro_elements )
                    n_st = declare_stream()  # Stream for the averaging iteration 'n'

                    with for_(n, 0, n < self.shot_num, n + 1):
                        with for_each_( op_idx, [0, 1]):  
                            with for_(*from_array(a, self.amps)):
                            # Play the 1st sequence with varying DRAG coefficient                   
                                # Init
                                if self.initializer is None:
                                    wait(100*u.us)
                                    #wait(thermalization_time * u.ns)
                                else:
                                    try:
                                        self.initializer[0](*self.initializer[1])
                                    except:
                                        print("Initializer didn't work!")
                                        wait(100*u.us)


                                # Operation
                                with switch_(op_idx, unsafe=True):
                                    with case_(0):
                                        # positive
                                        for xy in self.xy_elements:
                                            for _ in range(self.sequence_repeat):
                                                play("x180" * amp(1, 0, 0, a), xy)
                                                play("y90" * amp(a, 0, 0, 1), xy)
                                    with case_(1):
                                        # nagtive
                                        for xy in self.xy_elements:
                                            for _ in range(self.sequence_repeat):
                                                play("y180" * amp(a, 0, 0, 1), xy)
                                                play("x90" * amp(1, 0, 0, a), xy)

                                # Align the two elements to measure after playing the qubit pulses.
                                align()  # Global align between the two sequences
                                # Measurement
                                multiRO_measurement(iqdata_stream, self.ro_elements, weights="rotated_")

                        save(n, n_st)
                        
                    with stream_processing():
                        # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
                        multiRO_pre_save(iqdata_stream, self.ro_elements, (2,amp_len))
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
                sequence = ["x180","x90"]
            case 'freq':
                param_name = 'time'
                param_val = self.time_ns
                sequence = [self.virtial_detune_freq, -self.virtial_detune_freq]
            case 'drag':
                param_name = 'drag_coef'
                param_val = self.amps
                sequence = ["x180_y90","y180_x90"]
        output_data = {}
        for r_idx, r_name in enumerate(self.ro_elements):
            output_data[r_name] = ( ["mixer", "sequence", param_name],
                                np.array([self.fetch_data[r_idx*2], self.fetch_data[r_idx*2+1]]))
        dataset = xr.Dataset(
            output_data,
            coords={"mixer":np.array(["I","Q"]), 'sequence': sequence, param_name: param_val}
        )

        return dataset
            
    def _lin_freq_array( self ):

        freq_r1_qua = self.freq_range[0] * u.MHz
        freq_r2_qua = self.freq_range[1] * u.MHz
        freq_resolution_qua = self.freq_resolution * u.MHz
        freqs_qua = np.arange(freq_r1_qua,freq_r2_qua,freq_resolution_qua )
        
        return freqs_qua
            
    def _lin_time_array( self ):

        ramsey_period = abs(1e3/ self.virtial_detune_freq )* u.ns
        qua_cc_resolution = (ramsey_period//(4*self.point_per_period))
        if qua_cc_resolution < 1:
            print("Warning qua_cc_resolution <1 force to 1, virtial_detune_freq is to large or point_per_period is too large.")
            qua_cc_resolution = 1

        qua_cc_max_evo = qua_cc_resolution *self.point_per_period* self.max_period
        # print(f"time resolution {qua_cc_resolution*4} ,max time {evo_time_tick_max*4}")
        qua_cc_evo = np.arange( 4, qua_cc_max_evo, qua_cc_resolution)
        # evo_time = evo_time_tick*4
        
        return qua_cc_evo
        
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
