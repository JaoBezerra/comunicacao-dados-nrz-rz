import base64
import os

import numpy as np
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


CHARSET = "latin-1"

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
PBKDF2_ITERATIONS = 200_000


def text_to_bytes(message: str) -> bytes:
    try:
        return message.encode(CHARSET)
    except UnicodeEncodeError as exc:
        raise ValueError(
            "A mensagem contém caractere fora do Latin-1. "
            "Evite emojis e símbolos especiais não pertencentes ao ASCII estendido."
        ) from exc


def bytes_to_text(data: bytes) -> str:
    return data.decode(CHARSET)


def derive_key(password: str, salt: bytes) -> bytes:
    if not password:
        raise ValueError("A senha de criptografia não pode estar vazia.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )

    return kdf.derive(password.encode("utf-8"))


def encrypt_bytes(data: bytes, password: str) -> bytes:
    """
    Criptografia AES-256-GCM.

    O pacote final contém:
    salt de 16 bytes + nonce de 12 bytes + texto cifrado + tag de autenticação.

    A tag de autenticação é adicionada automaticamente ao final do ciphertext
    pela biblioteca AESGCM.
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    ciphertext = aesgcm.encrypt(nonce, data, associated_data=None)

    return salt + nonce + ciphertext


def decrypt_bytes(encrypted_package: bytes, password: str) -> bytes:
    """
    Processo inverso do AES-256-GCM.
    """
    minimum_size = SALT_SIZE + NONCE_SIZE + 16

    if len(encrypted_package) < minimum_size:
        raise ValueError("Pacote criptografado inválido ou incompleto.")

    salt = encrypted_package[:SALT_SIZE]
    nonce = encrypted_package[SALT_SIZE : SALT_SIZE + NONCE_SIZE]
    ciphertext = encrypted_package[SALT_SIZE + NONCE_SIZE :]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    try:
        return aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    except InvalidTag as exc:
        raise ValueError(
            "Falha na descriptografia. A senha está incorreta ou os dados foram alterados."
        ) from exc


def bytes_to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def bytes_to_binary(data: bytes) -> str:
    return "".join(format(byte, "08b") for byte in data)


def binary_to_bytes(binary_string: str) -> bytes:
    binary_string = binary_string.replace(" ", "")

    if len(binary_string) % 8 != 0:
        raise ValueError("A sequência binária não possui tamanho múltiplo de 8.")

    return bytes(
        int(binary_string[i : i + 8], 2)
        for i in range(0, len(binary_string), 8)
    )


def group_binary(binary_string: str, group_size: int = 8) -> str:
    binary_string = binary_string.replace(" ", "")

    return " ".join(
        binary_string[i : i + group_size]
        for i in range(0, len(binary_string), group_size)
    )


def encode_nrz(binary_string: str) -> np.ndarray:
    """
    NRZ unipolar:
    bit 1 -> +1 durante todo o intervalo do bit
    bit 0 ->  0 durante todo o intervalo do bit
    """
    signal = []

    for bit in binary_string:
        if bit == "1":
            signal.append(1.0)
        elif bit == "0":
            signal.append(0.0)
        else:
            raise ValueError("A sequência deve conter apenas bits 0 e 1.")

    return np.array(signal, dtype=np.float32)


def decode_nrz(signal: np.ndarray) -> str:
    bits = []

    for sample in signal:
        if sample > 0.5:
            bits.append("1")
        else:
            bits.append("0")

    return "".join(bits)


def encode_rz(binary_string: str) -> np.ndarray:
    """
    RZ polar:
    bit 1 -> +1 na primeira metade do bit, depois 0
    bit 0 -> -1 na primeira metade do bit, depois 0
    """
    signal = []

    for bit in binary_string:
        if bit == "1":
            signal.extend([1.0, 0.0])
        elif bit == "0":
            signal.extend([-1.0, 0.0])
        else:
            raise ValueError("A sequência deve conter apenas bits 0 e 1.")

    return np.array(signal, dtype=np.float32)


def decode_rz(signal: np.ndarray) -> str:
    if len(signal) % 2 != 0:
        raise ValueError("Sinal RZ inválido: quantidade ímpar de elementos.")

    bits = []

    for i in range(0, len(signal), 2):
        first_half = signal[i]

        if first_half > 0:
            bits.append("1")
        else:
            bits.append("0")

    return "".join(bits)


def encode_line_code(binary_string: str, algorithm: str) -> np.ndarray:
    algorithm = algorithm.upper()

    if algorithm == "NRZ":
        return encode_nrz(binary_string)

    if algorithm == "RZ":
        return encode_rz(binary_string)

    raise ValueError(f"Algoritmo não suportado: {algorithm}")


def decode_line_code(signal: np.ndarray, algorithm: str) -> str:
    algorithm = algorithm.upper()

    if algorithm == "NRZ":
        return decode_nrz(signal)

    if algorithm == "RZ":
        return decode_rz(signal)

    raise ValueError(f"Algoritmo não suportado: {algorithm}")


def process_message_to_signal(message: str, algorithm: str, password: str):
    """
    Fluxo do Host A:
    texto -> bytes Latin-1 -> AES-GCM -> binário -> NRZ/RZ.
    """
    original_bytes = text_to_bytes(message)
    encrypted_bytes = encrypt_bytes(original_bytes, password)
    binary_string = bytes_to_binary(encrypted_bytes)
    encoded_signal = encode_line_code(binary_string, algorithm)

    return {
        "original_bytes": original_bytes,
        "encrypted_bytes": encrypted_bytes,
        "binary_string": binary_string,
        "encoded_signal": encoded_signal,
    }


def recover_message_from_signal(signal: np.ndarray, algorithm: str, password: str):
    """
    Fluxo do Host B:
    sinal NRZ/RZ -> binário -> pacote AES-GCM -> texto original.
    """
    binary_string = decode_line_code(signal, algorithm)
    encrypted_bytes = binary_to_bytes(binary_string)
    original_bytes = decrypt_bytes(encrypted_bytes, password)
    original_message = bytes_to_text(original_bytes)

    return {
        "binary_string": binary_string,
        "encrypted_bytes": encrypted_bytes,
        "original_bytes": original_bytes,
        "original_message": original_message,
    }