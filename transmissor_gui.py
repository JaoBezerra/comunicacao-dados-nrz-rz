import customtkinter as ctk
import serial
import time
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from encoding_module import (
    bytes_to_base64,
    group_binary,
    process_message_to_signal,
    encode_line_code,
)
from visualization import plot_binary_signal, plot_signal_waveform

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TransmissorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Host A - Transmissor (Serial/ESP-NOW)")
        self.geometry("1100x700")

        # Configuração do Grid principal (Painel Lateral e Área Principal)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ================= PAINEL LATERAL (CONFIGURAÇÕES) =================
        self.sidebar_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        ctk.CTkLabel(self.sidebar_frame, text="Configurações", font=("Arial", 20, "bold")).pack(pady=(20, 10), padx=20)

        self.port_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Porta COM (ex: COM3)")
        self.port_entry.pack(pady=5, padx=20, fill="x")

        self.algo_var = ctk.StringVar(value="NRZ")
        ctk.CTkSegmentedButton(self.sidebar_frame, values=["NRZ", "RZ"], variable=self.algo_var).pack(pady=10, padx=20, fill="x")

        # Senha com botão Show/Hide
        pwd_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        pwd_frame.pack(pady=5, padx=20, fill="x")
        self.pwd_entry = ctk.CTkEntry(pwd_frame, placeholder_text="Senha AES-GCM", show="*")
        self.pwd_entry.insert(0, "senha_utfpr_2026")
        self.pwd_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.show_pwd_btn = ctk.CTkButton(pwd_frame, text="👁", width=30, command=self.toggle_password)
        self.show_pwd_btn.pack(side="right")

        # Modo Teste
        self.test_mode_var = ctk.BooleanVar(value=False)
        self.test_switch = ctk.CTkSwitch(self.sidebar_frame, text="Modo Teste (Sem Cripto)", variable=self.test_mode_var, command=self.toggle_test_mode)
        self.test_switch.pack(pady=10, padx=20, anchor="w")

        self.msg_label = ctk.CTkLabel(self.sidebar_frame, text="Mensagem / Binário:")
        self.msg_label.pack(padx=20, anchor="w")
        self.msg_entry = ctk.CTkEntry(self.sidebar_frame)
        self.msg_entry.insert(0, "Olá UTFPR")
        self.msg_entry.pack(pady=5, padx=20, fill="x")

        self.send_btn = ctk.CTkButton(self.sidebar_frame, text="Processar e Enviar", command=self.enviar_dados, fg_color="#28a745", hover_color="#218838")
        self.send_btn.pack(pady=20, padx=20, fill="x")

        # ================= ÁREA PRINCIPAL (VISUALIZAÇÃO) =================
        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.main_frame, text="Fluxo de Transmissão", font=("Arial", 24, "bold")).pack(pady=10)
        
        self.log_box = ctk.CTkTextbox(self.main_frame, height=250, font=("Consolas", 12))
        self.log_box.pack(fill="x", pady=5)
        
        self.graph_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.graph_frame.pack(fill="both", expand=True, pady=10)

    def toggle_password(self):
        if self.pwd_entry.cget("show") == "*":
            self.pwd_entry.configure(show="")
            self.show_pwd_btn.configure(text="🔒")
        else:
            self.pwd_entry.configure(show="*")
            self.show_pwd_btn.configure(text="👁")

    def toggle_test_mode(self):
        if self.test_mode_var.get():
            self.msg_entry.delete(0, "end")
            self.msg_entry.insert(0, "1100001000000000")
            self.msg_label.configure(text="Sequência Binária:")
        else:
            self.msg_entry.delete(0, "end")
            self.msg_entry.insert(0, "Olá UTFPR")
            self.msg_label.configure(text="Mensagem:")

    def log(self, title, content):
        self.log_box.insert("end", f"=== {title} ===\n{content}\n\n")
        self.log_box.see("end")

    def limpar_tela(self):
        self.log_box.delete("1.0", "end")
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

    def enviar_dados(self):
        port = self.port_entry.get()
        msg = self.msg_entry.get()
        algo = self.algo_var.get()
        pwd = self.pwd_entry.get()
        is_test = self.test_mode_var.get()

        if not port or not msg:
            self.log("ERRO", "Preencha a porta COM e a mensagem.")
            return

        self.limpar_tela()

        try:
            if is_test:
                msg = msg.replace(" ", "")
                if any(bit not in "01" for bit in msg):
                    self.log("ERRO", "No modo teste, insira apenas 0s e 1s.")
                    return
                binary_string = msg
                encoded_signal = encode_line_code(binary_string, algo)
                
                self.log("1. Modo Teste Ativo", "Criptografia e conversão ASCII ignoradas.")
                self.log("2. Sequência Binária de Teste", group_binary(binary_string))
            else:
                result = process_message_to_signal(msg, algo, pwd)
                encrypted_bytes = result["encrypted_bytes"]
                binary_string = result["binary_string"]
                encoded_signal = result["encoded_signal"]

                self.log("1. Mensagem Original", msg)
                self.log("2. Mensagem Criptografada (AES-GCM)", f"Base64: {bytes_to_base64(encrypted_bytes)}\nHex: {encrypted_bytes.hex(' ')}")
                self.log("3. Conversão para Binário (ASCII Estendido)", group_binary(binary_string))

            self.log(f"4. Aplicação do Algoritmo {algo}", str(encoded_signal.tolist()))

            # Gerar Gráficos
            samples_per_bit = 1 if algo == "NRZ" else 2
            
            fig_bits = plot_binary_signal(binary_string)
            canvas_bits = FigureCanvasTkAgg(fig_bits, master=self.graph_frame)
            canvas_bits.draw()
            canvas_bits.get_tk_widget().pack(fill="x", pady=5)

            fig_wave = plot_signal_waveform(encoded_signal, f"Forma de Onda {algo}", samples_per_bit)
            canvas_wave = FigureCanvasTkAgg(fig_wave, master=self.graph_frame)
            canvas_wave.draw()
            canvas_wave.get_tk_widget().pack(fill="x", pady=5)

            # Enviar via Serial
            # Novo Protocolo: ALGORITMO | TEST_MODE(1 ou 0) | SINAL _END_
            signal_str = ",".join(str(int(x)) for x in encoded_signal)
            test_flag = "1" if is_test else "0"
            full_payload = f"{algo}|{test_flag}|{signal_str}_END_"
            
            self.log("Status de Rede", f"Fragmentando pacote e enviando para ESP32 via porta {port}...")
            
            with serial.Serial(port, 115200, timeout=1) as ser:
                chunk_size = 150
                for i in range(0, len(full_payload), chunk_size):
                    chunk = full_payload[i:i+chunk_size] + "\n"
                    ser.write(chunk.encode('ascii'))
                    time.sleep(0.02)
            
            self.log("SUCESSO", "Pacote inteiramente despachado para o ESP32 Slave.")

        except Exception as e:
            self.log("ERRO FATAL", str(e))

if __name__ == "__main__":
    app = TransmissorApp()
    app.mainloop()