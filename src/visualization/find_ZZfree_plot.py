from qm.qua import *
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from analysis.find_ZZ_free_analysis import real_detune_X_flux, try_fit_ramsey, compute_fft, compute_fc

def plot_ZZfree(data, ax1=None, ax2=None):
    """
    data in shape (2,2,M,N)
    first 2 is postive and negative
    second 2 is postive and negative
    M is flux point
    N is evo_time_point
    """
    if ax1 is None or ax2 is None:
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(8, 10))

    flux, freq_X, freq_I = real_detune_X_flux(data)
    ZZfree_flux = flux[np.argmin(abs(freq_X - freq_I))]
    
    # Plot freq_X and freq_I on the first subplot
    ax1.set_xlabel("flux [V]")
    ax1.set_ylabel("Frequency [MHz]")
    ax1.plot(flux, freq_X, label="w/ X")
    ax1.plot(flux, freq_I, label="w/o X")
    ax1.legend()
    
    # Plot the difference freq_X - freq_I on the second subplot
    ax2.set_xlabel("flux [mV]")
    ax2.set_ylabel("Difference")
    ax2.plot(flux, freq_X - freq_I, label="diff")
    ax2.text(0.07, 0.9, f"min diff at : {ZZfree_flux:.3f}", fontsize=10, transform=ax2.transAxes)
    ax2.legend()
    
    plt.tight_layout()
    
    return ZZfree_flux

def plot_tau_X_flux(data):
    """
    Plot tau X flux data.
    
    Parameters:
    data (xarray.Dataset): Data in shape (2, 2, M, N)
        - The first 2 corresponds to positive and negative.
        - The second 2 corresponds to positive and negative.
        - M is the flux point.
        - N is the evolutionary time point.
    """
    flux = data.coords["flux"].values
    time = data.coords["time"].values
    q = list(data.data_vars.keys())[0]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Tau X Flux Data')

    labels = [["X-Positive", "X-Negative"],
              ["I-Positive", "I-Negative"]]
    
    for i in range(2):
        for j in range(2):
            ax = axes[i, j]
            c = ax.pcolormesh(flux, time, data[q][0, i, j, :, :].T, cmap='RdBu', shading='auto')
            ax.set_title(labels[i][j])
            ax.set_xlabel('Flux [V]')
            ax.set_ylabel('Evolutionary Time [ns]')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])

def plot_pureZZ(data):
    """
    Plot tau X flux data.
    
    Parameters:
    data (xarray.Dataset): Data in shape (M, N)
        - M is the flux point.
        - N is the evolutionary time point.
    """
    flux = data.coords["flux"].values
    time = data.coords["time"].values
    q = list(data.data_vars.keys())[0]
    Crosstalk = np.zeros(len(flux))
    for i in range(len(Crosstalk)):
        # fft_values, frequencies = compute_fft(data[q][0, i, :])
        # idx_max_freq = np.argmax(np.abs(fft_values[1:len(fft_values)//2])) + 1
        # Crosstalk[i] = frequencies[idx_max_freq]

        Crosstalk[i] = try_fit_ramsey(data[q][0, i, :])


    ZZfree_flux = flux[np.argmin(abs(Crosstalk))]

    # fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(8, 15))
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(15, 8))

    c = ax1.pcolormesh(flux, time, data[q][0, :, :].T, cmap='RdBu', shading='auto')
    ax1.set_title("Tau X Flux")
    ax1.set_ylabel('Evolutionary Time [ns]')
    # fig.colorbar(c, ax=ax1, label='Intensity')  # 添加 colorbar

    ax2.plot(flux, Crosstalk, label="Crosstalk", color='blue')
    ax2.set_title("Crosstalk X Flux")
    ax2.set_xlabel("Flux [V]")
    ax2.set_ylabel("Crosstalk [MHz]")
    ax2.text(0.07, 0.9, f"min crosstalk at : {ZZfree_flux:.3f}", fontsize=10, transform=ax2.transAxes)
    
    # ax3.plot(flux, compute_fc(flux, 7.323, 4.663579, 0.225, 0.132), label="fc", color='blue')
    # ax3.set_title("fc(z) X Flux")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    return fig

def plot_crosstalk_X_frequency(data):
    """
    Plot crosstalk X frequency data.
    
    Parameters:
    data (xarray.Dataset): Data in shape (M, N)
        - M is the flux point.
        - N is the evolutionary time point.
    """
    flux = data.coords["flux"].values
    q = list(data.data_vars.keys())[0]
    Crosstalk = np.zeros(len(flux))
    for i in range(len(Crosstalk)):
        fft_values, frequencies = compute_fft(data[q][0, i, :])
        idx_max_freq = np.argmax(np.abs(fft_values[1:len(fft_values)//2])) + 1
        Crosstalk[i] = frequencies[idx_max_freq]

        # Crosstalk[i] = try_fit_ramsey(data[q][0, i, :])

    ZZfree_flux = flux[np.argmin(abs(Crosstalk))]

    fc_pos = compute_fc(flux[flux >= 0], 7.323, 4.663579, 0.225, 0.132)
    fc_neg = compute_fc(flux[flux < 0], 7.323, 4.663579, 0.225, 0.132)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(fc_pos, Crosstalk[flux >= 0], label="Positive Flux", color='red')
    ax.plot(fc_neg, Crosstalk[flux < 0], label="Negative Flux", color='blue')

    ax.set_title("Crosstalk X Coupler Frequency")
    ax.set_xlabel('Coupler Frequency [GHz]')
    ax.set_ylabel('Crosstalk [MHz]')
    ax.text(0.07, 0.9, f"Min crosstalk at : {compute_fc(ZZfree_flux, 7.323, 4.663579, 0.225, 0.132):.3f}", fontsize=10, transform=ax.transAxes)
    ax.legend()
    ax.grid(True)

def plot_1D_ramsey(data):
    """
    Plot 1D ramsey (flux in middle) data.
    
    Parameters:
    data (xarray.Dataset): Data in shape (M, N)
        - M is the flux point.
        - N is the evolutionary time point.
    """
    q = list(data.data_vars.keys())[0]
    flux = data.coords["flux"].values
    time = data.coords["time"].values
    fig, ax = plt.subplots()
    print(flux[len(flux)//2])
    try_fit_ramsey(data[q][0, len(flux)//2, :])
    ax.plot(time, data[q][0, len(flux)//2, :], "o")
    ax.set_xlabel("Free Evolution Times [ns]")
    ax.legend()

    if ax == None:
        return fig

def plot_fft(data):
    """
    繪製原始信號及其最大頻率分量的時域表示，並繪製FFT結果。

    參數：
    data : xarray.DataArray
        包含時間點和數據點的xarray DataArray。
    """
    q = list(data.data_vars.keys())[0]
    flux = data.coords["flux"].values
    data = data[q][0, len(flux)//2, :]

    fft_values, frequencies = compute_fft(data)
    
    # 找到最大頻率分量
    idx_max_freq = np.argmax(np.abs(fft_values[1:len(fft_values)//2])) + 1
    max_freq = frequencies[idx_max_freq]
    evo_time = data.coords["time"].values
    max_amplitude = np.abs(fft_values[idx_max_freq]) / (len(data) / 2)
    max_freq_component = max_amplitude * np.cos(2 * np.pi * max_freq * evo_time + np.angle(fft_values[idx_max_freq])) + np.mean(data.values)
    
    data_values = data.values
    n = len(data_values)
    
    # 繪圖
    plt.figure(figsize=(12, 8))

    # 繪製原始信號及其最大頻率分量的時域表示
    plt.subplot(2, 1, 1)
    plt.plot(evo_time, data_values, label='原始信號')
    plt.plot(evo_time, max_freq_component, label=f'最大頻率分量 (頻率 = {max_freq:.2f} Hz)', linestyle='--', color='r')
    plt.legend()
    plt.title('原始信號及其最大頻率分量的時域表示')
    plt.xlabel('時間')
    plt.ylabel('幅值')

    # 繪製FFT結果
    plt.subplot(2, 1, 2)
    plt.plot(frequencies[:n//2], np.abs(fft_values)[:n//2] * 2 / n)
    plt.title('FFT結果')
    plt.xlabel('頻率 (Hz)')
    plt.ylabel('幅值')

    plt.tight_layout()


def plot_fc(z, fc_max, fq, z_fq, Ec):
    fc = compute_fc(z, fc_max, fq, z_fq, Ec)
    plt.figure(figsize=(10, 6))
    plt.plot(z, fc, label='fc(z)')
    plt.xlabel('z')
    plt.ylabel('fc(z)')
    plt.legend()
    plt.grid(True)
    plt.show()


