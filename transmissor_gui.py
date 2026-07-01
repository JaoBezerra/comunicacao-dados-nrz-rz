import customtkinter as ctk
import serial
import time
import numpy as np
from encoding_module import process_message_to_signal

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TransmissorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Host A - Transmissor (Serial/ESP-NOW)")
        self.geometry("500x500")

        ctk.CTkLabel(self, text="Transmissor NRZ/RZ", font=("Arial", 20, "bold")).pack(pady=10)

        self.port_entry = ctk.CTkEntry(self, placeholder_text="Porta COM (ex: COM3 ou /dev/ttyUSB0)", width=300)
        self.port_entry.pack(pady=5)

        self.algo_var = ctk.StringVar(value="NRZ")
        ctk.CTkSegmentedButton(self, values=["NRZ", "RZ"], variable=self.algo_var).pack(pady=10)

        self.pwd_entry = ctk.CTkEntry(self, placeholder_text="Senha AES-GCM", show="*", width=300)
        self.pwd_entry.insert(0, "senha_utfpr_2026")
        self.pwd_entry.pack(pady=5)

        self.msg_entry = ctk.CTkEntry(self, placeholder_text="Digite a mensagem...", width=300)
        self.msg_entry.pack(pady=10)

        self.send_btn = ctk.CTkButton(self, text="Enviar via ESP32", command=self.enviar_dados)
        self.send_btn.pack(pady=20)

        self.log_box = ctk.CTkTextbox(self, width=450, height=150)
        self.log_box.pack(pady=5)

    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def enviar_dados(self):
        port = self.port_entry.get()
        msg = self.msg_entry.get()
        algo = self.algo_var.get()
        pwd = self.pwd_entry.get()

        if not port or not msg:
            self.log("ERRO: Preencha a porta e a mensagem.")
            return

        try:
            self.log("Processando mensagem...")
            result = process_message_to_signal(msg, algo, pwd)
            encoded_signal = result["encoded_signal"]
            
            # Converte o array de floats [1.0, 0.0, -1.0] em uma string compacta "1,0,-1"
            signal_str = ",".join(str(int(x)) for x in encoded_signal)
            
            # Adicionamos a flag _END_ para o receptor saber que o sinal acabou
            full_payload = f"{algo}:{signal_str}_END_"
            
            self.log("Enviando dados para a Serial em chunks...")
            with serial.Serial(port, 115200, timeout=1) as ser:
                chunk_size = 150 # Seguro para o ESP-NOW
                for i in range(0, len(full_payload), chunk_size):
                    chunk = full_payload[i:i+chunk_size] + "\n"
                    ser.write(chunk.encode('ascii'))
                    time.sleep(0.02) # Dá tempo ao ESP32 para despachar via rádio
            
            self.log("Envio concluído com sucesso!")

        except Exception as e:
            self.log(f"ERRO: {str(e)}")

if __name__ == "__main__":
    app = TransmissorApp()
    app.mainloop()