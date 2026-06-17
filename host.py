import json
import socket

import streamlit as st

from encoding_module import (
    bytes_to_base64,
    group_binary,
    process_message_to_signal,
    encode_line_code,
)
from visualization import plot_binary_signal, plot_signal_waveform


def send_payload(receiver_ip: str, port: int, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    size = len(data).to_bytes(4, byteorder="big")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((receiver_ip, port))
        sock.sendall(size + data)


st.set_page_config(page_title="Host A - Transmissor", layout="wide")

st.title("Host A - Transmissor NRZ/RZ")

st.markdown(
    """
Este lado executa o processo de envio:

**mensagem original → criptografia → binário ASCII estendido → NRZ/RZ → gráfico → rede**
"""
)

with st.sidebar:
    st.header("Configurações")

    algorithm = st.radio(
        "Algoritmo de codificação de linha:",
        ["NRZ", "RZ"],
        index=0,
    )
    
    password = st.text_input(
        "Senha AES-GCM:",
        value="senha_utfpr_2026",
        type="password",
)

    receiver_ip = st.text_input(
        "IP do Host B:",
        value="",
        placeholder="Exemplo: 192.168.0.25",
    )

    port = st.number_input(
        "Porta:",
        min_value=1024,
        max_value=65535,
        value=65432,
        step=1,
    )

    test_mode = st.toggle(
        "Modo teste sem criptografia",
        value=False,
        help="Usado para testar a sequência binária da aula sem criptografia.",
    )

samples_per_bit = 1 if algorithm == "NRZ" else 2

if test_mode:
    st.subheader("Modo teste")

    test_binary = st.text_input(
        "Sequência binária de teste:",
        value="1100001000000000",
    ).replace(" ", "")

    if any(bit not in "01" for bit in test_binary):
        st.error("A sequência de teste deve conter apenas 0 e 1.")
        st.stop()

    binary_string = test_binary
    encoded_signal = encode_line_code(binary_string, algorithm)

    st.write("**Criptografia:** pulada no modo teste.")
    st.write("**Conversão ASCII:** pulada no modo teste.")
    st.write("**Binário de teste:**")
    st.code(group_binary(binary_string))

else:
    st.subheader("Mensagem")

    message = st.text_input(
        "Digite a mensagem:",
        value="Olá UTFPR",
    )

    if not message:
        st.info("Digite uma mensagem para iniciar.")
        st.stop()

    try:
        result = process_message_to_signal(message, algorithm, password)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    encrypted_bytes = result["encrypted_bytes"]
    binary_string = result["binary_string"]
    encoded_signal = result["encoded_signal"]

    st.subheader("1. Mensagem original")
    st.write(message)

    st.subheader("2. Mensagem criptografada")
    st.write("Representação Base64 do pacote criptografado:")
    st.code(bytes_to_base64(encrypted_bytes))

    st.write("Representação hexadecimal do pacote criptografado:")
    st.code(encrypted_bytes.hex(" "))

    st.subheader("3. Mensagem em binário usando ASCII estendido")
    st.code(group_binary(binary_string))

st.subheader(f"4. Aplicação do algoritmo {algorithm}")
st.write("Sequência de níveis do sinal:")
st.code(encoded_signal.tolist())

col1, col2 = st.columns(2)

with col1:
    st.subheader("Gráfico dos bits")
    binary_fig = plot_binary_signal(binary_string)
    st.pyplot(binary_fig)

with col2:
    st.subheader(f"Forma de onda {algorithm}")
    signal_fig = plot_signal_waveform(
        encoded_signal,
        title=f"Forma de onda codificada em {algorithm}",
        samples_per_bit=samples_per_bit,
    )
    st.pyplot(signal_fig)

st.markdown("---")

if st.button("Enviar para o Host B", use_container_width=True):
    if not receiver_ip:
        st.error("Informe o IP real do Host B. Não use localhost na apresentação.")
        st.stop()

    payload = {
        "algorithm": algorithm,
        "signal": encoded_signal.tolist(),
        "test_mode": test_mode,
        "charset": "latin-1",
        "crypto": "AES-256-GCM",
    }

    try:
        send_payload(receiver_ip, int(port), payload)
        st.success(f"Mensagem enviada para {receiver_ip}:{port}")
    except Exception as exc:
        st.error(f"Erro ao enviar: {exc}")