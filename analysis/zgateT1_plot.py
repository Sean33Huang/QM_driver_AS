import os
import xarray as xr
from numpy import array, std, average, round, max, min, transpose, abs, sqrt, cos, sin, pi, linspace, arange,ndarray, log10
import matplotlib.pyplot as plt 
from matplotlib.ticker import FuncFormatter
from exp.relaxation_time import fit_T1

dir_path = "/Users/ratiswu/Downloads/ZgateT1"
fqs_meas = [5.34, 4.4]
bias_meas = [0.165+0.0009, 0.165+0.0009-0.0435]



def zgate_T1_fitting(dataset:xr.Dataset):
    
    time = dataset.coords["time"].values
    flux = dataset.coords["z_voltage"].values

    T1s = []
    
    for ro_name, data in dataset.data_vars.items():
        signals = data.values[0]
        
        for zDepData in data.values[0]:
            
            try:
                T1s.append(round(fit_T1(time,zDepData)[0]*1e-3,1))
            except:
                T1s.append(1e-6)
            
    return time/1000, flux, T1s, signals

def set_fit_paras(): # **** manually set
    d = 0.6
    Ec = 0.3 #GHz
    Ej_sum = 25
    init = (Ec,Ej_sum,d)
    up_b = (0.31,50,1)
    lo_b = (0.29,10,0)

    return init, lo_b, up_b

def inver(lis:list):
    return 1/array(lis)

def FqEqn(x,Ec,coefA,d):
    """
    a ~ period, b ~ offset, 
    """
    a = pi/0.175
    b = 0.165+0.0009
    return sqrt(8*coefA*Ec*sqrt(cos(a*(x-b))**2+d**2*sin(a*(x-b))**2))-Ec


def plot_z_gateT1_poster(dir_path:str,sweet_bias:float,other_bias:list=None, other_bias_label:str=None, flux_cav_nc_path:str=None):
    
    # res = []

    # # Iterate directory
    # x_path = "/Users/ratiswu/Downloads/ZgateT1_wopi_1"
    # for path in os.listdir(x_path):
    #     # check if current path is a file
    #     if os.path.isfile(os.path.join(x_path, path)):
    #         res.append(os.path.join(x_path,path))



    # sets = []
    # for file in res:
    #     sets.append(xr.open_dataset(file))


    # T1 = []
    # I_chennel = []
    # for dataset in sets:
        
    #     # for dataset in sub_set:
    #     time, biass, T1s, Isignal = zgate_T1_fitting(dataset)
    #     T1.append(T1s)
    #     I_chennel.append(Isignal)
        

    # avg_I_data = average(array(I_chennel),axis=0)
    # z = biass+sweet_bias
    # ============================ keep below 
    # list to store files
    res = []

    # Iterate directory
    for path in os.listdir(dir_path):
        # check if current path is a file
        if os.path.isfile(os.path.join(dir_path, path)):
            res.append(os.path.join(dir_path,path))



    sets = []
    for file in res:
        sets.append(xr.open_dataset(file))


    T1 = []
    I_chennel = []
    for dataset in sets:
        
        # for dataset in sub_set:
        time, bias, T1s, Isignal = zgate_T1_fitting(dataset)
        T1.append(T1s)
        I_chennel.append(Isignal)


    
    avg_I_data = average(array(I_chennel),axis=0)
    z = bias+sweet_bias

    # Fit t1 with the whole averaging I signal
    T1_1 = []
    for zDepData in avg_I_data:
        T1_1.append(round(fit_T1(time*1e3,zDepData)[0]*1e-3,1))


    avg_T1 = average(array(T1),axis=0)
    std_T1_percent = round(std(array(T1),axis=0)*100/avg_T1,1)

    plots_max_n = 5
    if flux_cav_nc_path is None:
        plots_max_n -= 1
        if len(fqs_meas) == 1:
            plots_max_n -= 1
            flx_cav_plot_idx= 3
            flx_qub_plt_idx = 4
        else:
            flx_cav_plot_idx= 4
            flx_qub_plt_idx = 3
    else:
        if len(fqs_meas) == 1:
            plots_max_n -= 1
            flx_cav_plot_idx= 3
            flx_qub_plt_idx = 4
        else:
            flx_cav_plot_idx= 3
            flx_qub_plt_idx = 4
    
    fig, ax = plt.subplots(plots_max_n,1,figsize=(12.5,22))

    im = ax[0].pcolormesh(z,time,transpose(avg_I_data),cmap='RdBu')
    ax[0].scatter(z,avg_T1,s=3,label='$T_{1}$',c='#0000FF')
   
    if other_bias is not None:
        ax[0].vlines(other_bias,0,50,colors='black',linestyles="--",label=other_bias_label)
    ax[0].vlines([sweet_bias],0,50,colors='orange',linestyles="--",label='Fq=5.3GHz')
    # ax[0].set_xlim(0.035,0.08) 
    ax[0].set_xlabel("bias (V)")
    ax[0].set_ylabel("Free Evolution time(µs)") 
    ax[0].set_ylim(0,50)
    ax[0].set_title("$T_{1}$ vs Z-bias, in 10 average")
    ax[0].legend(loc='lower left')
    # fig.colorbar(im, ax=ax[0])
    rate = inver(avg_T1)
    ax[1].scatter(z,rate,s=3)
    if other_bias is not None:
        ax[1].vlines(other_bias,0,max(rate),colors='black',linestyles="--")
    ax[1].vlines([sweet_bias],0,max(rate),colors='orange',linestyles="--")

    # ax[1].set_xlabel("bias (V)")
    ax[1].set_ylabel("$\Gamma_{1}$ (MHz)") 
    ax[1].set_ylim(1/50,1/8)
    ax[1].set_title("$\Gamma_{1}$ vs Z-bias, in 10 average")

    ax[2].plot(z,std_T1_percent)
    # ax[2].set_xlabel("bias (V)")
    ax[2].set_ylabel("STD Percentage (%)")
    ax[2].set_title("STD vs Z-bias, in 10 average")
    if other_bias is not None:
        ax[2].vlines(other_bias,0,100,colors='black',linestyles="--")
    ax[2].vlines([sweet_bias],0,100,colors='orange',linestyles="--")
    ax[2].set_ylim(0,100)



    if flux_cav_nc_path is not None:
        dataset = xr.open_dataset(flux_cav_nc_path)
        for ro, data in dataset.data_vars.items():

            amp = data[0] + 1j*data[1]
            freq = (dataset.coords["frequency"].values+5762)/1000 # ***
            flux = dataset.coords["flux"].values
            ax[flx_cav_plot_idx].pcolormesh(flux,freq,abs(amp),cmap='RdBu')
            ax[flx_cav_plot_idx].set_xlim(min(z),max(z))
            ax[flx_cav_plot_idx].set_ylim(5.7525,5.765)                          # ***
            ax[flx_cav_plot_idx].set_ylabel("Frequency (GHz)")
            ax[flx_cav_plot_idx].set_title("Flux dependent Cavity")
            if other_bias is not None:
                ax[flx_cav_plot_idx].vlines(other_bias,min(freq),max(freq),colors='black',linestyles="--")
            ax[flx_cav_plot_idx].vlines([sweet_bias],min(freq),max(freq),colors='orange',linestyles="--")


    if len(fqs_meas) >= 2 and len(bias_meas) >= 2:
        from scipy.optimize import curve_fit 
        init, lo_b, up_b = set_fit_paras()
        p, e = curve_fit(FqEqn,bias_meas,fqs_meas,p0=init,bounds=(lo_b,up_b))

        fq = FqEqn(z,*p)
        print("fq sweetspot: ",FqEqn(array([sweet_bias]),*p))
        ax[flx_qub_plt_idx].plot(z,fq)
        ax[flx_qub_plt_idx].set_title(f"Ec={round(p[0],3)} GHz, Ej={round(p[1],1)} GHz, d={round(p[2],2)}")
        ax[flx_qub_plt_idx].vlines([bias_meas[1]],min(fq),fqs_meas[1],colors='black',linestyles="--")
        ax[flx_qub_plt_idx].vlines([bias_meas[0]],min(fq),fqs_meas[0],colors='orange',linestyles="--")
        ax[flx_qub_plt_idx].set_xlabel("bias (V)")
        ax[flx_qub_plt_idx].set_ylabel("$f_{q}$ (GHz)")
        ax[flx_qub_plt_idx].set_title("Flux dependent Transition Frequency")


    peak_fq_z = array([0.151588, 0.142654, 0.136175, 0.131079, 0.126723, 0.122809, 
                 0.119167, 0.1157939,0.112661, 0.109920])
    
    peak_fq = FqEqn(peak_fq_z,*p)
    
    from numpy import diff, mean
    dif = diff(peak_fq)*1000
    print("peak fq @ ",peak_fq)
    print("that differences: ",dif)
    print(f"avg diff = {round(mean(dif),3)} +/- {round(std(dif),3)} MHz")

    plt.tight_layout()
    # plt.savefig("/Users/ratiswu/Downloads/ZgateT1_welldone.png")
    plt.show()
    # plt.close()
    if other_bias is not None:
        return fq, p, z, rate, std_T1_percent
    else:
        return [], [], z, rate, std_T1_percent
    


from numpy import ndarray

def plot_purcell_compa(fq:ndarray,p:list,z:ndarray,sweet_bias:float, rate:ndarray, std_T1_percent:ndarray):
    min_fq = min(fq)
    max_fq = max(fq)
    a = FqEqn(array([0.035]),*p)
    b = FqEqn(array([0.08]),*p)

    x_value = FqEqn(z,*p)

    fq1 = []
    fq12 = []
    fq2 = []
    for i in range(z.shape[0]):
        if z[i] < sweet_bias:
            fq1.append(i)
        elif z[i] > sweet_bias:
            fq2.append(i)
        else:
            fq12.append(i)

    fq = []
    gamma = []
    sd = []
    if len(fq1)>=len(fq2):
        fq1_ = fq1[(len(fq1)-len(fq2)):]
        fq1_.reverse()
        fq2 = fq2[1:]
        a = []
        for idx in range(len(fq2)):
            fq_l = FqEqn(array([z[fq1_[idx]]]),*p)[0]
            fq_r = FqEqn(array([z[fq2[idx]]]),*p)[0]
            a = (fq_l-fq_r)*100/((fq_l+fq_r)/2)
            if abs(a) < 1e-9: # 1Hz
                fq.append(fq_l)
                
                sd.append((std_T1_percent[fq1_[idx]]+std_T1_percent[fq2[idx]])/2)



    fq_max = max(x_value)*1e3
    fb = 5.76045e3
    g = 52.57
    delta_min = fb-fq_max
    kappa = ((38)**(-1))*((g/delta_min)**(-2))
    a = g/(sqrt(fb*fq_max))
    def gamma_purcell(fq:ndarray,fb:float,a:float,kappa:float):
        return array(kappa*((a**2)*fq*fb)/((fb**2)-2*fq*fb+(fq**2)))

    print(gamma_purcell(fq_max,fb,a,kappa)**(-1))
    print(max(x_value))

    # fq = x_value
    gamma = rate
    # sd = std_T1_percent
    gamma_p = gamma_purcell(x_value*1e3,fb,a,kappa)

    fig ,ax = plt.subplots(2,1,)
    ax[0].scatter(x_value,gamma,s=3,c='red',label="$\Gamma_{1}$")
    ax[0].plot(x_value,gamma_p,label="$\Gamma_{purcell}$")
    ax[0].set_ylabel("$\Gamma_{1}$ (MHz)") 
    # ax[0].set_yscale("log")
    # ax[0].set_ylim(1e-2,2e-1)
    ax[0].set_ylim(0.002,0.2)
    ax[0].set_title("$\Gamma_{1}$ vs Transition frequency, in 10 average")
    ax[0].set_xlabel("Transition Frequency (GHz)")
    ax[0].set_xlim(4,5.3)
    # ax[0].vlines([4.4],-0.05,max(gamma),colors='black',linestyles="--")
    # ax[0].vlines([5.3],0,max(gamma),colors='green',linestyles="--")
    ax[0].legend(loc='upper left')

    ax[1].scatter(x_value,(gamma-gamma_p)/gamma,s=3,label="$\Gamma_{other}$",c='green')
    ax[1].scatter(x_value,gamma_p/gamma,s=3,label="$\Gamma_{purcell}$")
    ax[1].set_ylim(0,1)
    ax[1].set_xlim(4,5.3)
    # ax[1].set_yscale("log")
    ax[1].legend()
    ax[1].set_xlabel("Transition Frequency (GHz)")
    ax[1].set_ylabel("Ratio")


    # ax[1].plot(fq,sd)
    # ax[1].set_ylabel("STD Percentage (%)")
    # ax[1].set_title("STD vs Transition frequency, in 10 average")
    # ax[1].vlines([4.4],0,100,colors='black',linestyles="--")
    # ax[1].vlines([5.3],0,100,colors='orange',linestyles="--")
    # ax[1].set_ylim(0,100)
    # ax[1].set_xlabel("Transition Frequency (GHz)")




    plt.tight_layout()
    # plt.savefig("/Users/ratiswu/Downloads/ZgateT1_welldone_part3.png")
    plt.show()
    # plt.close()


# from numpy import ndarray, asarray

# def find_nearest_idx(array, value):
#     array = asarray(array)
#     idx = (abs(array - value)).argmin()
#     return idx

# def give_Z_plotT1(z:list,flux_ary:ndarray,time:ndarray,Isignals:ndarray):
#     """
#     z is a list contains what bias T1 you want to see,\n
#     Isignals.shape = (flux, evoTime)
#     """
#     fig, ax = plt.subplots(len(z),1)
#     for idx in range(len(z)):
#         z_idx = find_nearest_idx(flux_ary, z[idx])
#         target_data = Isignals[z_idx]
#         T1, func = fit_T1(time,target_data)
#         ax[idx].scatter(time,target_data)
#         ax[idx].plot( time, func(time), label=f"{z[idx]}: T1={round(T1,1)}µs")
#         ax[idx].legend(loc='upper right')
#     plt.xlabel("Evolution time (µs)")
#     plt.ylabel("I chennel (mV)")
#     plt.show()


# # give_Z_plotT1([0.08,0.04533338,-0.02],z,time,avg_I_data)


if __name__ == "__main__":
    fq, p, z, rate, std_T1_percent = plot_z_gateT1_poster(dir_path,bias_meas[0],[bias_meas[1]],"fq=4.4GHz")
    plot_purcell_compa(fq, p, z, bias_meas[0], rate, std_T1_percent)