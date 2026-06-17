import json
import socket
import subprocess
import platform

import numpy as np
import streamlit as st

from encoding_module import (
    bytes_to_base64,
    bytes_to_text,
    decrypt_bytes,
    binary_to_bytes,
    decode_line_code,
    group_binary,
)
from visualization import plot_binary_signal, plot_signal_waveform


def get_local_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
        sock.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


def get_network_interfaces():
    interfaces = []

    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                encoding="cp850",
                errors="ignore",
            )

            current_interface = None

            for line in result.stdout.splitlines():
                lower_line = line.lower()

                if "adaptador" in lower_line or "adapter" in lower_line:
                    current_interface = line.strip().replace(":", "")

                if "ipv4" in lower_line and ":" in line:
                    ip = line.split(":")[-1].strip()
                    ip = ip.replace("(Preferencial)", "").strip()

                    if ip and not ip.startswith("127."):
                        interfaces.append((current_interface or "Interface", ip))
        else:
            result = subprocess.run(
                ["hostname", "-I"],
                capture_output=True,
                text=True,
            )

            for index, ip in enumerate(result.stdout.split()):
                if not ip.startswith("127."):
                    interfaces.append((f"Interface {index + 1}", ip))

    except Exception:
        pass

    return interfaces


def receive_exact(conn, size):
    data = b""

    while len(data) < size:
        packet = conn.recv(size - len(data))

        if not packet:
            raise ConnectionError("Conexão encerrada antes do recebimento completo.")

        data += packet

    return data


def receive_payload(port: int, bind_ip: str, timeout: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_ip, port))
        sock.listen(1)
        sock.settimeout(timeout)

        conn, addr = sock.accept()

        with conn:
            size_bytes = receive_exact(conn, 4)
            payload_size = int.from_bytes(size_bytes, byteorder="big")
            payload_data = receive_exact(conn, payload_size)

        payload = json.loads(payload_data.decode("utf-8"))

    return payload, addr


st.set_page_config(page_title="Host B - Receptor", layout="wide")

st.title("Host B - Receptor NRZ/RZ")

st.markdown(
    """
Este lado executa o processo inverso:

**recepção → gráfico → decodificação NRZ/RZ → binário → ASCII estendido → descriptografia → mensagem original**
"""
)

local_ip = get_local_ip()
interfaces = get_network_interfaces()

st.info(f"IP principal deste computador: `{local_ip}`")

with st.expander("Interfaces de rede detectadas"):
    if interfaces:
        for name, ip in interfaces:
            st.write(f"- **{name}:** `{ip}`")
    else:
        st.warning("Nenhuma interface adicional detectada.")

with st.sidebar:
    st.header("Configurações")

    port = st.number_input(
        "Porta de escuta:",
        min_value=1024,
        max_value=65535,
        value=65432,
        step=1,
    )

    password = st.text_input(
        "Senha AES-GCM:",
        value="senha_utfpr_2026",
        type="password",
        help="Deve ser igual à senha usada no Host A.",
    )

    bind_option = st.selectbox(
        "Interface de escuta:",
        ["0.0.0.0"] + [ip for _, ip in interfaces] + ["127.0.0.1"],
        index=0,
    )

    timeout = st.number_input(
        "Timeout de escuta, em segundos:",
        min_value=5,
        max_value=120,
        value=30,
        step=5,
    )

st.write("Configure o Host A com:")
st.code(f"IP do Host B: {local_ip}\nPorta: {int(port)}")

if st.button("Aguardar mensagem", use_container_width=True):
    status = st.empty()
    status.info(f"Aguardando conexão em {bind_option}:{int(port)}...")

    try:
        payload, addr = receive_payload(int(port), bind_option, int(timeout))
    except socket.timeout:
        st.error("Tempo esgotado. Nenhuma mensagem foi recebida.")
        st.stop()
    except Exception as exc:
        st.error(f"Erro ao receber mensagem: {exc}")
        st.stop()

    status.success(f"Mensagem recebida de {addr[0]}:{addr[1]}")

    algorithm = payload["algorithm"]
    signal = np.array(payload["signal"], dtype=np.float32)
    test_mode = payload.get("test_mode", False)
    samples_per_bit = 1 if algorithm == "NRZ" else 2

    st.subheader(f"1. Sinal recebido ({algorithm})")
    st.code(signal.tolist())

    signal_fig = plot_signal_waveform(
        signal,
        title=f"Forma de onda recebida em {algorithm}",
        samples_per_bit=samples_per_bit,
    )
    st.pyplot(signal_fig)

    try:
        binary_string = decode_line_code(signal, algorithm)
    except ValueError as exc:
        st.error(f"Erro na decodificação {algorithm}: {exc}")
        st.stop()

    st.subheader("2. Binário recuperado")
    st.code(group_binary(binary_string))

    binary_fig = plot_binary_signal(binary_string, title="Bits recuperados")
    st.pyplot(binary_fig)

    if test_mode:
        st.subheader("3. Resultado do modo teste")
        st.success("Sequência binária recuperada com sucesso.")
        st.write("Como o modo teste não usa criptografia nem ASCII, o processo termina no binário.")
        st.stop()

    try:
        encrypted_bytes = binary_to_bytes(binary_string)

        decrypted_bytes = decrypt_bytes(encrypted_bytes, password)
        original_message = bytes_to_text(decrypted_bytes)

    except Exception as exc:
        st.error(f"Erro ao reconstruir a mensagem: {exc}")
        st.stop()

    st.subheader("3. Mensagem criptografada recuperada")
    st.write("Representação Base64 do pacote criptografado:")
    st.code(bytes_to_base64(encrypted_bytes))

    st.write("Pacote criptografado em hexadecimal:")
    st.code(encrypted_bytes.hex(" "))

    st.subheader("4. Mensagem original recuperada")
    st.success(original_message)