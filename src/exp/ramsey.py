from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
import matplotlib.pyplot as plt
from qualang_tools.loops import from_array
from qualang_tools.results import fetching_tool, progress_counter
from qualang_tools.plot import interrupt_on_close
from exp.RO_macros import multiRO_declare, multiRO_measurement, multiRO_pre_save
from qualang_tools.plot.fitting import Fit
# from common_fitting_func import *
import numpy as np
from scipy.optimize import curve_fit
import warnings
warnings.filterwarnings("ignore")
from qualang_tools.units import unit
u = unit(coerce_to_integer=True)
import xarray as xr

def exp_ramsey(time_max,time_resolution,ro_element,xy_element,n_avg,config,qmm,virtual_detune=0,simulate:bool=False,initializer=None) -> xr.Dataset:
    """

    virtual_detune unit in MHz.\n
    time_max unit in us.\n
    time_resolution unit in us.\n
    """
    v_detune_qua = virtual_detune *u.MHz
    print(virtual_detune)
    cc_resolution = (time_resolution/4.) *u.us
    cc_max_qua = (time_max/4.) *u.us
    cc_qua = np.arange( 4, cc_max_qua, cc_resolution)
    print(cc_qua)

    evo_time = cc_qua*4
    time_len = len(cc_qua)
    with program() as ramsey:
        iqdata_stream = multiRO_declare( ro_element )
        n = declare(int)
        n_st = declare_stream()
        cc = declare(int)  # QUA variable for the idle time, unit in clock cycle
        phi = declare(fixed)  # Phase to apply the virtual Z-rotation
        with for_(n, 0, n < n_avg, n + 1):
            with for_( *from_array(cc, cc_qua) ):
                
                    # Init
                    if initializer is None:
                        wait(100*u.us)
                    else:
                        try:
                            initializer[0](*initializer[1])
                        except:
                            print("Initializer didn't work!")
                            wait(100*u.us)

                    # Operation
                    phi = Cast.mul_fixed_by_int( virtual_detune/1e3, 4 *cc)
                    # True_value =  v_detune_qua*4*cc
                    # False_value = v_detune_qua*4*cc

                    for xy in xy_element:
                        play("x90", xy)  # 1st x90 gate
                        wait(cc, xy)
                        frame_rotation_2pi(phi, xy)  # Virtual Z-rotation
                        play("x90", xy)  # 2st x90 gate

                    # Align after playing the qubit pulses.
                    align()
                    # Readout
                    multiRO_measurement(iqdata_stream, ro_element, weights="rotated_")         
                

            # Save the averaging iteration to get the progress bar
            save(n, n_st)

        with stream_processing():
            n_st.save("iteration")
            multiRO_pre_save(iqdata_stream, ro_element, (time_len,) )

    ###########################
    # Run or Simulate Program #
    ###########################


    if simulate:
        # Simulates the QUA program for the specified duration
        simulation_config = SimulationConfig(duration=20_000)  # In clock cycles = 4ns
        job = qmm.simulate(config, ramsey, simulation_config)
        job.get_simulated_samples().con1.plot()
        job.get_simulated_samples().con2.plot()
        plt.show()

    else:
        # Open the quantum machine
        qm = qmm.open_qm(config)
        # Send the QUA program to the OPX, which compiles and executes it
        job = qm.execute(ramsey)
        # Get results from QUA program
        ro_ch_name = []
        for r_name in ro_element:
            ro_ch_name.append(f"{r_name}_I")
            ro_ch_name.append(f"{r_name}_Q")
        data_list = ro_ch_name + ["iteration"]   
        results = fetching_tool(job, data_list=data_list, mode="live")
        # Live plotting

        fig, ax = plt.subplots(2, len(ro_element))
        interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
        fig.suptitle("Frequency calibration")

        # Live plotting
        while results.is_processing():
            # Fetch results
            fetch_data = results.fetch_all()
            # output_data = {}
            # for r_idx, r_name in enumerate(ro_element):
            #     ax[r_idx*2].cla()
            #     ax[r_idx*2+1].cla()
            #     output_data[r_name] = np.array([fetch_data[r_idx*2], fetch_data[r_idx*2+1]])

            #     # Plot I
            #     ax[r_idx*2].set_ylabel("I quadrature [V]")
            #     plot_ramsey_oscillation(evo_time, output_data[r_name][0], ax[r_idx*2])
            #     # Plot Q
            #     ax[r_idx*2+1].set_ylabel("Q quadrature [V]")
            #     plot_ramsey_oscillation(evo_time, output_data[r_name][1], ax[r_idx*2+1])

    
            # Progress bar
            iteration = fetch_data[-1]
            progress_counter(iteration, n_avg, start_time=results.start_time)
            # Plot
            plt.tight_layout()
            plt.pause(1)

        # Measurement finished 
        fetch_data = results.fetch_all()
        qm.close()
        output_data = {}

        for r_idx, r_name in enumerate(ro_element):
            output_data[r_name] = ( ["mixer","time"],
                                np.array([fetch_data[r_idx*2], fetch_data[r_idx*2+1]]) )
        dataset = xr.Dataset(
            output_data,
            coords={ "mixer":np.array(["I","Q"]), "time": evo_time }
        )

        return dataset
       
def T2_fitting(idle_times, signal, plot_or_not:bool=True)->float:
    """
    idle_times is the real time.
    """
    try:
        fit = Fit()
        decay_fit = fit.ramsey(idle_times, signal, plot=plot_or_not)
        qubit_T2 = np.round(np.abs(decay_fit["T2"][0]),1) 
    except Exception as e:     
        print(f"An error occurred: {e}")  
        qubit_T2 = 0
    return qubit_T2

def multi_T2_exp(m, Qi, n_avg,idle_times,operation_flux_point,q_id,qmm):
    T2_I, T2_Q = [], []
    for i in range(m):
        I, Q = exp_ramsey(Qi,n_avg,idle_times,operation_flux_point,q_id,qmm)
        T2_I.append(T2_fitting(I))
        T2_Q.append(T2_fitting(Q))
        print(f'iteration: {i+1}')
    return T2_I, T2_Q

def plot_ramsey_oscillation( x, y, ax=None ):
    """
    y in shape (2,N)
    2 is postive and negative
    N is evo_time_point
    """
    if ax == None:
        fig, ax = plt.subplots()
    ax.plot(x, y, "-",label="positive")
    ax.set_xlabel("Free Evolution Times [ns]")
    ax.legend()
    if ax == None:
        return fig
# def T2_hist(data, T2_max, signal_name):
#     try:
#         new_data = [x / 1000 for x in data]  
#         bin_width = 0.5  
#         start_value = -0.25  
#         end_value = T2_max + 0.25  
#         custom_bins = [start_value + i * bin_width for i in range(int((end_value - start_value) / bin_width) + 1)]
#         hist_values, bin_edges = np.histogram(new_data, bins=custom_bins, density=True)
#         bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
#         params, covariance = curve_fit(gaussian, bin_centers, hist_values)
#         mu, sigma = params
#         plt.cla()
#         plt.hist(new_data, bins=custom_bins, density=True, alpha=0.7, color='blue', label='Histogram') 
#         xmin, xmax = plt.xlim()
#         x = np.linspace(xmin, xmax, 100)
#         p = gaussian(x, mu, sigma)
#         plt.plot(x, p, 'k', linewidth=2, label=f'Fit result: $\mu$={mu:.2f}, $\sigma$={sigma:.2f}')
#         plt.legend()
#         plt.title('T2_'+signal_name+' Gaussian Distribution Fit')
#         plt.show()
#         print(f'Mean: {mu:.2f}')
#         print(f'Standard Deviation: {sigma:.2f}')
#     except Exception as e:
#         print(f"An error occurred: {e}")


# 2024/06/06 added by Ratis
def statistic_T2_exp(repeat:int,max_time:float,time_resolution:float,q_name:list,ro_element:list,config,qmm:QuantumMachinesManager,n_avg:int=100,initializer=None,virtual_detune:float=1e-6):
    """
    ### Return\n
    2D ndarray with the shape (2,M):\n
    1) axis 0 is I and Q chennels.\n
    2) axis 1 is repeat times M.
    """ 
    statistic_T2 = {}
    raw_data = {}
    repetition = np.arange(repeat)
    for res in ro_element:
        statistic_T2[res] = []
        raw_data[res] = []
    for i in range(repeat):
        print(f"The {i}th T2")
        dataset:xr.Dataset = exp_ramsey(max_time, time_resolution, ro_element, q_name, n_avg, config, qmm, virtual_detune, False, initializer, live=True if repeat==1 else False)
        time = dataset.coords["time"].values()
        for ro_name, data in dataset.data_vars.items():
            print(min(time), max(time))
            T2_i = T2_fitting(time, data[0], True if repeat==1 else False)
            print(f"{ro_name} T2 = {T2_i}")
            statistic_T2[ro_name].append([T2_i])
            raw_data[ro_name].append(data)
    if repeat == 1 :
        plt.show()
    else:
        plt.close()
    output_data = {}
    for res in ro_element:
        statistic_T2[res] = np.array(statistic_T2[res]).transpose()[0]
        output_data[res] = (["repetition","mixer","time"],np.array(raw_data[res]))
    
    dataset = xr.Dataset(output_data, coords={"mixer":np.array(["I","Q"]), "time":time, "repetition":repetition}).transpose("mixer","repetition","time")

    return statistic_T2, dataset


if __name__ == '__main__':
    from configuration import *

    n_avg = 750
    idle_times = np.arange(4, 200, 1)  
    detuning = 1e6  
    operation_flux_point = [0, -3.000e-01, -0.2525, -0.3433, -3.400e-01] 
    q_id = [0,1,2,3]
    Qi = 3

    qmm = QuantumMachinesManager(host=qop_ip, port=qop_port, cluster_name=cluster_name, octave=octave_config)
    I,Q = T2_exp(Qi,n_avg,idle_times,operation_flux_point,q_id,qmm)
    T2_plot(I, Q, Qi, True)
    # m = 3
    # T2_I, T2_Q = multi_T2_exp(m, Qi, n_avg,idle_times,operation_flux_point,q_id,qmm)
    # T2_hist(T2_I,15,'I')
    # T2_hist(T2_Q,15,'Q')