import matplotlib.pyplot as plt
import numpy as np


def plot_signal_waveform(signal, title="Forma de onda", samples_per_bit=1):
    signal = np.array(signal, dtype=float)

    fig, ax = plt.subplots(figsize=(14, 4))

    if len(signal) == 0:
        ax.set_title(title)
        return fig

    x = np.arange(len(signal) + 1)
    y = np.append(signal, signal[-1])

    ax.step(x, y, where="post", linewidth=2)

    ax.axhline(0, linewidth=1)
    ax.grid(True, linestyle="--", alpha=0.5)

    ax.set_title(title)
    ax.set_xlabel("Elementos de sinal")
    ax.set_ylabel("Amplitude")

    ax.set_ylim(min(-1.5, signal.min() - 0.5), max(1.5, signal.max() + 0.5))
    ax.set_xlim(0, len(signal))

    for i, value in enumerate(signal):
        ax.text(
            i + 0.5,
            value + 0.08 if value >= 0 else value - 0.18,
            f"{value:.0f}",
            ha="center",
            fontsize=8,
        )

    if samples_per_bit > 1:
        for bit_boundary in range(0, len(signal) + 1, samples_per_bit):
            ax.axvline(bit_boundary, linestyle=":", alpha=0.3)

    fig.tight_layout()
    return fig


def plot_binary_signal(binary_string, title="Representação binária"):
    binary_string = binary_string.replace(" ", "")
    bits = [int(bit) for bit in binary_string]

    fig, ax = plt.subplots(figsize=(14, 3))

    if len(bits) == 0:
        ax.set_title(title)
        return fig

    x = np.arange(len(bits) + 1)
    y = np.append(bits, bits[-1])

    ax.step(x, y, where="post", linewidth=2)
    ax.fill_between(x, y, step="post", alpha=0.2)

    ax.set_title(title)
    ax.set_xlabel("Bits")
    ax.set_ylabel("Nível lógico")
    ax.set_ylim(-0.2, 1.2)
    ax.set_xlim(0, len(bits))
    ax.grid(True, linestyle="--", alpha=0.5)

    for i, bit in enumerate(bits):
        ax.text(i + 0.5, bit + 0.08, str(bit), ha="center", fontsize=8)

    fig.tight_layout()
    return fig