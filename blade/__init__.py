import os
import sys
import time
from pathlib import Path

from bladerf import _bladerf
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.fftpack import fft, fftshift
from flask import current_app

# BladeRF Settings
SAMPLE_RATE = 2.5e6  # 2.5 MHz
FREQ = 4612e6         # 915 MHz (ISM Band
SAMPLE_COUNT = 2000  # Number of samples per read
GAIN = 50            # RX Gain
CHANNEL = 2          # MIMO Channel

def probe_bladerf():
    device_handle: object = None
    print("Searching for bladeRF devices...")

    try:
        device_info_list: list = _bladerf.get_device_list()

        if(len(device_info_list) == 1):
            device_handle = "{backend}:device={usb_bus}:{usb_addr}".format(**device_info_list[0]._asdict())
            print("Found bladeRF device: " + str(device_handle))
        else:
            print("Unsupported feature: more than one bladeRFs detected.")
            print("\n".join([str(device_info) for device_info in device_info_list]))

    except _bladerf.BladeRFError:
        print("No bladeRF devices found.")
        pass

    return device_handle

def configure_bladerf(device_handle: object):
    """ Configures the BladeRF device """
    device: object = _bladerf.BladeRF(device_handle)

    device.sync_config(
        layout=_bladerf.ChannelLayout.RX_X1,
        fmt=_bladerf.Format.SC16_Q11,
        num_buffers=16,
        buffer_size=8192,
        num_transfers=8,
        stream_timeout=3500
    )

    return device

def plot_signal(iq_samples, sample_rate):
    """ Plots the time and frequency domain of the received signal """
    time_axis = np.arange(len(iq_samples))

    # Frequency Domain Processing
    fft_data = fftshift(fft(iq_samples))
    freq_axis = np.linspace(-sample_rate/2, sample_rate/2, len(iq_samples))

    #matplotlib.use('module://mpl_ascii')
    plt.figure(figsize=(12, 6))

    # Time Domain Plot
    plt.subplot(2, 1, 1)
    plt.plot(time_axis[:500], iq_samples.real[:500], label="I (Real)")
    plt.plot(time_axis[:500], iq_samples.imag[:500], label="Q (Imag)")
    plt.title("Time Domain Signal")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.legend()

    # Frequency Domain Plot
    plt.subplot(2, 1, 2)
    plt.plot(freq_axis / 1e6, np.abs(fft_data), color="red")
    plt.title("Frequency Spectrum")
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Magnitude")

    plt.tight_layout()
    plt.show()

    output_file: str = os.path.join(Path(current_app.root_path).parent, 'web', 'static', 'images', 'graph.png')
    plt.savefig(output_file, dpi=300)
    plt.close()

def setup_device():
    #_bladerf.set_verbosity(1)

    # Setup the BladeRF device.
    device_handle: object = probe_bladerf()
    device=configure_bladerf(device_handle=device_handle)

    channel: object = device.Channel(CHANNEL)
    channel.frequency = FREQ
    channel.sample_rate = SAMPLE_RATE
    channel.gain = GAIN
    channel.enable = True

    return device

def draw_graph(device):
    # IQ samples (interleaved)
    samples: object = np.zeros(SAMPLE_COUNT * 2, dtype=np.int16)

    device.sync_rx(buf=samples, num_samples=2000, timeout_ms=5000)

    # Convert to complex numbers
    iq_samples = samples[0::2] + 1j * samples[1::2]

    plot_signal(iq_samples=iq_samples, sample_rate=SAMPLE_RATE)

