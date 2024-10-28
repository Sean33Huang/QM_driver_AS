"""
        SINGLE QUBIT RANDOMIZED BENCHMARKING (for gates >= 40ns)
The program consists in playing random sequences of Clifford gates and measuring the state of the resonator afterwards.
Each random sequence is derived on the FPGA for the maximum depth (specified as an input) and played for each depth
asked by the user (the sequence is truncated to the desired depth). Each truncated sequence ends with the recovery gate,
found at each step thanks to a preloaded lookup table (Cayley table), that will bring the qubit back to its ground state.

If the readout has been calibrated and is good enough, then state discrimination can be applied to only return the state
of the qubit. Otherwise, the 'I' and 'Q' quadratures are returned.
Each sequence is played n_avg times for averaging. A second averaging is performed by playing different random sequences.

The data is then post-processed to extract the single-qubit gate fidelity and error per gate
.
Prerequisites:
    - Having found the resonance frequency of the resonator coupled to the qubit under study (resonator_spectroscopy).
    - Having calibrated qubit pi pulse (x180) by running qubit, spectroscopy, rabi_chevron, power_rabi and updated the config.
    - Having the qubit frequency perfectly calibrated (ramsey).
    - (optional) Having calibrated the readout (readout_frequency, amplitude, duration_optimization IQ_blobs) for better SNR.
    - Set the desired flux bias.
"""

from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig
from scipy.optimize import curve_fit

import matplotlib.pyplot as plt
import numpy as np
from qualang_tools.bakery.randomized_benchmark_c1 import c1_table
inv_gates = [int(np.where(c1_table[i, :] == 0)[0][0]) for i in range(24)]

from qualang_tools.results import fetching_tool, progress_counter
from qualang_tools.plot import interrupt_on_close
import warnings
warnings.filterwarnings("ignore")
from qualang_tools.units import unit
u = unit(coerce_to_integer=True)

from exp.RO_macros import multiRO_declare, multiRO_measurement, multiRO_pre_save

from matplotlib.figure import Figure

#######################
# AUXILIARY FUNCTIONS #
#######################
import time

###################################
# Helper functions and QUA macros #
###################################

import xarray as xr
from exp.QMMeasurement import QMMeasurement

class randomized_banchmarking_interleaved_sq(QMMeasurement):
    def __init__( self, config, qmm: QuantumMachinesManager):
        super().__init__( config, qmm )
        self.xy_elements = None
        self.ro_elements = None
        self.gate_length = 40
        self.max_circuit_depth = 200
        self.base_clifford = 2
        self.initializer = None
        self.n_avg = 100
        self.state_discrimination = False
        self.interleaved_gate_index = 2
        self.initialization_macro = False
        self.seed = None
        self.threshold = 0
        self.x = np.array([])

    def _get_qua_program(self):

        gate_num = 1
        gate_step = 0
        while gate_num <= self.max_circuit_depth:
            self.x = np.append(self.x, [gate_num])
            gate_step = gate_step + 1
            gate_num = self.base_clifford * gate_num
        ###################
        # The QUA program #
        ###################
        with program() as rb:
            depth = declare(int)  # QUA variable for the varying depth
            depth_target = declare(int)  # QUA variable for the current depth (changes in steps of delta_clifford)
            # QUA variable to store the last Clifford gate of the current sequence which is replaced by the recovery gate
            saved_gate = declare(int)
            m = declare(int)  # QUA variable for the loop over random sequences
            n = declare(int)  # QUA variable for the averaging loop
            a = declare(fixed)  # QUA variable for the DRAG coefficient pre-factor
            iqdata_stream = multiRO_declare( self.ro_elements )
            n_st = declare_stream()  # Stream for the averaging iteration 'n'
            state = [declare(bool) for _ in range(len(self.ro_elements))]  # QUA variable for state discrimination
            # The relevant streams
            m_st = declare_stream()

    
            if self.state_discrimination:
                state_st = [declare_stream() for _ in range(self.ro_elements)]

            with for_(m, 0, m < self.shot_num, m + 1):  # QUA for_ loop over the random sequences
                sequence_list, inv_gate_list = self._generate_sequence()  # Generate the random sequence of length max_circuit_depth

                assign(depth_target, 2)  # Initialize the current depth to 0

                with for_(depth, 1, depth <= 2 * self.max_circuit_depth, depth + 1):  # Loop over the depths
                    # Replacing the last gate in the sequence with the sequence's inverse gate
                    # The original gate is saved in 'saved_gate' and is being restored at the end
                    assign(saved_gate, sequence_list[depth])
                    assign(sequence_list[depth], inv_gate_list[depth - 1])
                    # Only played the depth corresponding to target_depth
                    with if_((depth == depth_target)):
                        with for_(n, 0, n < self.n_avg, n + 1):
                            # Initialize
                            wait(100 * u.us)
                            if self.initialization_macro:
                                wait(100 * u.us)
                            else:
                                pass
                                # initialization_macro()
                            align()

                            # Operation
                            # The strict_timing ensures that the sequence will be played without gaps
                            with strict_timing_():
                                # Play the random sequence of desired depth
                                for xy in self.xy_elements:
                                    self._play_sequence(sequence_list, depth, xy)
                            # Align the two elements to measure after playing the circuit.
                            align()

                            # Make sure you updated the ge_threshold and angle if you want to use state discrimination
                            multiRO_measurement(iqdata_stream, self.ro_elements, weights="rotated_")
                            # Make sure you updated the ge_threshold
                            if self.state_discrimination:
                                for idx_res, res in enumerate(self.ro_elements):
                                    assign(state[idx_res], iqdata_stream[0][idx_res] > self.threshold)
                                    save(state[idx_res], state_st[idx_res])

                        # Go to the next depth
                        assign(depth_target, self.base_clifford * depth_target)
                    # Reset the last gate of the sequence back to the original Clifford gate
                    # (that was replaced by the recovery gate at the beginning)
                    assign(sequence_list[depth], saved_gate)
                # Save the counter for the progress bar
                save(m, m_st)

            with stream_processing():
                m_st.save("iteration")

                (I, I_st, Q, Q_st) = iqdata_stream
                if type(self.ro_elements) is not list:
                    self.ro_elements = [self.ro_elements]
                
                for idx_res, res in enumerate(self.ro_elements):
                    if self.state_discrimination:
                        # saves a 2D array of depth and random pulse sequences in order to get error bars along the random sequences
                        state_st[idx_res].boolean_to_int().buffer(self.n_avg).map(FUNCTIONS.average()).buffer(
                            gate_step
                        ).buffer(self.shot_num).save(f"{res}_state")
                        # returns a 1D array of averaged random pulse sequences vs depth_inl of circuit for live plotting
                        state_st[idx_res].boolean_to_int().buffer(self.n_avg).map(FUNCTIONS.average()).buffer(
                            gate_step
                        ).average().save(f"{res}_state_avg")
                    else:
                        # multiRO_pre_save(iqdata_stream_inl, ro_elements, (gate_step,2) )
                        I_st[idx_res].buffer(self.n_avg).map(FUNCTIONS.average()).buffer(gate_step).buffer(
                            self.shot_num
                        ).save(f"{res}_I")
                        Q_st[idx_res].buffer(self.n_avg).map(FUNCTIONS.average()).buffer(gate_step).buffer(
                            self.shot_num
                        ).save(f"{res}_Q")
                        I_st[idx_res].buffer(self.n_avg).map(FUNCTIONS.average()).buffer(gate_step).average().save(
                            f"{res}_I_avg"
                        )
                        Q_st[idx_res].buffer(self.n_avg).map(FUNCTIONS.average()).buffer(gate_step).average().save(
                            f"{res}_Q_avg"
                        )

        return rb
    
    def _get_fetch_data_list( self ):
        ro_ch_name = []
        for r_name in self.ro_elements:
            if self.state_discrimination:
                ro_ch_name.append(f"{r_name}_state")
            else:
                ro_ch_name.append(f"{r_name}_I")
                ro_ch_name.append(f"{r_name}_Q")
            data_list = ro_ch_name + ["iteration"]
        return data_list

    def _data_formation( self ):

        output_data = {}
        for r_idx, r_name in enumerate(self.ro_elements):
            if self.state_discrimination:
                state = self.fetch_data[r_idx]
                value_avg = np.mean(state, axis=0)
                error_avg = np.std(state, axis=0)
                
                output_data[r_name] = ( ["mixer","x"],
                    np.array([value_avg,error_avg]) )
            else:
                I = self.fetch_data[r_idx*2]
                value_avg = np.mean(I, axis=0)
                error_avg = np.std(I, axis=0)
                output_data[r_name] = ( ["mixer","x"],
                    np.array([value_avg,error_avg]))
                

        dataset = xr.Dataset(
            output_data,
            coords={ "mixer":np.array(["val","err"]), "x":self.x}
        )

        return dataset

    def _generate_sequence( self ):
        cayley = declare(int, value=c1_table.flatten().tolist())
        inv_list = declare(int, value=inv_gates)
        current_state = declare(int)
        step = declare(int)
        sequence = declare(int, size=2 * self.max_circuit_depth + 1)
        inv_gate = declare(int, size=2 * self.max_circuit_depth*2 + 1)
        i = declare(int)
        if self.seed is None: self.seed = 345324
        rand = Random(seed=self.seed)

        assign(current_state, 0)
        with for_(i, 0, i < 2 * self.max_circuit_depth, i + 2):
            assign(step, rand.rand_int(24))
            assign(current_state, cayley[current_state * 24 + step])
            assign(sequence[i], step)
            assign(inv_gate[i], inv_list[current_state])
            # interleaved gate
            assign(step, self.interleaved_gate_index)
            assign(current_state, cayley[current_state * 24 + step])
            assign(sequence[i + 1], step)
            assign(inv_gate[i + 1], inv_list[current_state])    

        return sequence, inv_gate

    def _play_sequence(self, sequence_list, depth, xy):
        i = declare(int)
        with for_(i, 0, i <= depth, i + 1):
            with switch_(sequence_list[i], unsafe=True):
                with case_(0):
                    wait(self.gate_length // 4, xy)
                with case_(1):
                    play("x180", xy)
                with case_(2):
                    play("y180", xy)
                with case_(3):
                    play("y180", xy)
                    play("x180", xy)
                with case_(4):
                    play("x90", xy)
                    play("y90", xy)
                with case_(5):
                    play("x90", xy)
                    play("-y90", xy)
                with case_(6):
                    play("-x90", xy)
                    play("y90", xy)
                with case_(7):
                    play("-x90", xy)
                    play("-y90", xy)
                with case_(8):
                    play("y90", xy)
                    play("x90", xy)
                with case_(9):
                    play("y90", xy)
                    play("-x90", xy)
                with case_(10):
                    play("-y90", xy)
                    play("x90", xy)
                with case_(11):
                    play("-y90", xy)
                    play("-x90", xy)
                with case_(12):
                    play("x90", xy)
                with case_(13):
                    play("-x90", xy)
                with case_(14):
                    play("y90", xy)
                with case_(15):
                    play("-y90", xy)
                with case_(16):
                    play("-x90", xy)
                    play("y90", xy)
                    play("x90", xy)
                with case_(17):
                    play("-x90", xy)
                    play("-y90", xy)
                    play("x90", xy)
                with case_(18):
                    play("x180", xy)
                    play("y90", xy)
                with case_(19):
                    play("x180", xy)
                    play("-y90", xy)
                with case_(20):
                    play("y180", xy)
                    play("x90", xy)
                with case_(21):
                    play("y180", xy)
                    play("-x90", xy)
                with case_(22):
                    play("x90", xy)
                    play("y90", xy)
                    play("x90", xy)
                with case_(23):
                    play("-x90", xy)
                    play("y90", xy)
                    play("-x90", xy)