from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
import matplotlib.pyplot as plt
from qualang_tools.loops import from_array
from qualang_tools.results import fetching_tool
from qualang_tools.plot import interrupt_on_close
from qualang_tools.results import progress_counter
from qualang_tools.plot.fitting import Fit
# from common_fitting_func import gaussian
import exp.config_par as gc
from scipy.optimize import curve_fit
import warnings
from exp.RO_macros import multiRO_declare, multiRO_measurement, multiRO_pre_save
import xarray as xr
warnings.filterwarnings("ignore")
from qualang_tools.units import unit
u = unit(coerce_to_integer=True)
import time
from exp.QMMeasurement import QMMeasurement

class single_spin_echo( QMMeasurement ):
    def __init__( self, config, qmm: QuantumMachinesManager):
        super().__init__( config, qmm )
        self.time_range = [4,400] 

        """evo time is the duration between x90 and x180, unit in nano seconds
          I want the program to try spin echo for different time durations"""
        
        self.time_resolution = 10
        self.q_name = None
        self.ro_element = None
        self.n_avg = 100
        self.initializer = None
        self.simulate = False

    def _get_qua_program( self ):
        time_r1_qua = (self.time_range[0]/4) *u.ns
        time_r2_qua = (self.time_range[1]/4) *u.ns

        if self.time_resolution < 4:
            print( "Warning!! time resolution < 4 ns.")
        time_resolution_qua = (self.time_resolution/4) *u.ns
        self.qua_driving_time = np.arange(time_r1_qua, time_r2_qua, time_resolution_qua)
        
        # QUA program
        with program() as spin_echo:

            iqdata_stream = multiRO_declare( self.ro_element )
            half_evo_time = declare(int)  # x180 -> x90 has same time duration as x90 -> x180
            n = declare(int)
            n_st = declare_stream()
            with for_(n, 0, n < self.n_avg, n + 1):
                with for_(*from_array(half_evo_time, self.qua_driving_time)):
                    # initializaion
                    if self.initializer is None:
                        wait(1*u.us,self.ro_element)
                    else:
                        try:
                            self.initializer[0](*self.initializer[1])
                        except:
                            wait(1*u.us,self.ro_element)

                    # Operation: x90 -> x180 -> x-90, should theoretically project to |0>    
                    for q in self.q_name:
                        play("x90", q)
                        wait(half_evo_time)
                        play("x180", q)  
                        wait(half_evo_time)  
                        play("x-90",q)

                    # Readout
                    multiRO_measurement( iqdata_stream,  resonators=self.ro_element, weights="rotated_")
                
                # Save the averaging iteration to get the progress bar
                save(n, n_st)

            with stream_processing():
                n_st.save("iteration")
                multiRO_pre_save(iqdata_stream, self.ro_element, (self.qua_driving_time.shape[-1], ))

        return spin_echo

    def _get_fetch_data_list( self ):
            ro_ch_name = []
            for r_name in self.ro_elements:
                ro_ch_name.append(f"{r_name}_I")
                ro_ch_name.append(f"{r_name}_Q")

            data_list = ro_ch_name + ["iteration"]   
            return data_list
    
    def _data_formation( self ):
        output_data = {}
        qua_driving_time = self.qua_driving_time*4 #4 for scaling back to normal dimension
        for r_idx, r_name in enumerate(self.ro_element):
            output_data[r_name] = ( ["mixer","half_evolution_time"],
                                np.array([self.fetch_data[r_idx*2], self.fetch_data[r_idx*2+1]]) )
        dataset = xr.Dataset(
            output_data,
            coords={ "mixer":np.array(["I","Q"]), "half_evolution_time": qua_driving_time }
        )
    
        # cannot think of attributes for this experiment so far
        return dataset