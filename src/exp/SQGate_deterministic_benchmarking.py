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

class SQGate_deterministic_benchmarking( QMMeasurement ):

    def __init__( self, config, qmm: QuantumMachinesManager ):
        super().__init__( config, qmm )
        self.ro_elements = ['q4_ro']
        self.xy_elements = ['q4_xy']

        self.sequence_repeat = 500

        self.initializer = None
        self.gate = 1
        # 1 = X X
        # 2 = X -X
        # 3 = Y Y
        # 4 = Y -Y

    def _get_qua_program(self):

        pulse1, pulse2 = self._pulse_sequence()

        with program() as qua_prog:
            n = declare(int)  # QUA variable for the averaging loop
            rep = declare(int)  # QUA variable for the measured 'repeat' quadrature
            iqdata_stream = multiRO_declare( self.ro_elements )
            n_st = declare_stream()  # Stream for the averaging iteration 'n'

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
                    
                    i = declare(int)
                    for xy in self.xy_elements:
                        play('y90', xy)
                        with for_(i, 0, i < rep, i + 1):
                            play(pulse1, xy)
                            play(pulse2, xy)
                        play('-y90', xy)

                    align()
                    # Readout
                    multiRO_measurement(iqdata_stream, self.ro_elements, weights="rotated_")         
                    
                save(n, n_st)
            with stream_processing():
                # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
                multiRO_pre_save(iqdata_stream, self.ro_elements, (self.sequence_repeat,) )
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

        param_name = 'repeat_time'
        param_val = np.arange(0, self.sequence_repeat, 1)

        output_data = {}
        for r_idx, r_name in enumerate(self.ro_elements):
            output_data[r_name] = ( ["mixer",param_name],
                                np.array([self.fetch_data[r_idx*2], self.fetch_data[r_idx*2+1]]))
        dataset = xr.Dataset(
            output_data,
            coords={ "mixer":np.array(["I","Q"]) , param_name: param_val}
        )

        return dataset
    
    def _pulse_sequence(self):
        match self.gate:
            case 1:
                return "x180", "x180"
            case 2:
                return "x180", "-x180"
            case 3:
                return "y180", "y180"
            case 4:
                return "y180", "-y180"

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
