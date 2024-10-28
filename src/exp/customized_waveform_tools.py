import numpy as np

def multi_sine_pulse_waveforms(
    amplitude, length, anharmonicity, detuning=0.0, **kwargs
):
    """
    Creates Cosine based DRAG waveforms that compensate for the leakage and for the AC stark shift.

    These DRAG waveforms has been implemented following the next Refs.:
    Chen et al. PRL, 116, 020501 (2016)
    https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.020501
    and Chen's thesis
    https://web.physics.ucsb.edu/~martinisgroup/theses/Chen2018.pdf

    :param float amplitude: The amplitude in volts.
    :param int length: The pulse length in ns.
    :param float alpha: The DRAG coefficient.
    :param float anharmonicity: f_21 - f_10 - The differences in energy between the 2-1 and the 1-0 energy levels, in Hz.
    :param float detuning: The frequency shift to correct for AC stark shift, in Hz.
    :return: Returns a tuple of two lists. The first list is the I waveform (real part) and the second is the
        Q waveform (imaginary part)
    """
    wx2_amp = kwargs.get("wx2amp", 0)
    wx3_amp = kwargs.get("wx3amp", 0)
    wx4_amp = kwargs.get("wx4amp", 0)


    if anharmonicity == 0:
        raise Exception("Cannot create a DRAG pulse with `anharmonicity=0`")
    t = np.arange(length, dtype=int)  # An array of size pulse length in ns
    end_point = length - 1
    cos_wave = (
        0.5 * amplitude * (1 - np.cos(t * 2 * np.pi / end_point))
    )  # The cosine function
    sin_wave = (
        0.5 * amplitude * np.sin(t * np.pi / end_point)+
        0.5 * wx2_amp * np.sin(2 * t * np.pi / end_point)+
        0.5 * wx3_amp * np.sin(3 * t * np.pi / end_point)+
        0.5 * wx4_amp * np.sin(4 * t * np.pi / end_point)
    )  # The derivative of cosine function
    z = sin_wave + 1j * 0
    I_wf = z.real.tolist()  # The `I` component is the real part of the waveform
    Q_wf = (
        z.imag.tolist()
    )  # The `Q` component is the imaginary part of the waveform
    return I_wf, Q_wf

# --------------------------z pulse waveform----------------------------------

def z_sine_pulse_waveforms(
    amplitude, 
    length, 
    freq = 1,
    phase = 0,
    **kwargs
):
    """
    Creates sine waveforms.

    :param float amplitude: The amplitude in volts.
    :param int length: The pulse length in ns.
    :kwarg 'freq': frequency factor of sin. Default = 1, where sin pulse has frequency = 1/[2*(length-1)]
    :kwarg 'phase': phase shift of sin in degree. Default = 0.
    :return: Returns a tuple of one lists.
    """
    t = np.arange(length, dtype=int)  # An array of size pulse length in ns
    end_point = length - 1
    cos_wave = (
        amplitude * (1 - np.cos(t * 2 * np.pi / end_point))
    )  # The cosine function
    sin_wave = (
        amplitude * np.sin(freq * t * np.pi / end_point + phase/180 * np.pi)

    )  # The derivative of cosine function
    z = sin_wave + 1j * 0
    wf = z.real.tolist()  # The `I` component is the real part of the waveform

    return wf