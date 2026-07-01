import customtkinter as ctk
import serial
import threading
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from encoding_module import (
    bytes_to_base64,
    bytes_to_text,
    decrypt_bytes,
    binary_to_bytes,
    decode_line_code,
    group_binary,
)
from visualization import plot_binary_signal, plot_signal_waveform

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class ReceptorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Host B - Receptor (Serial/ESP-NOW)")
        self.geometry("1100x750")
        
        self.reading_serial = False
        self.accumulated_data = ""

        # Configuração do Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ================= PAINEL LATERAL =================
        self.sidebar_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar_frame, text="Receptor", font=("Arial", 20, "bold")).pack(pady=(20, 10))

        # Painel MAC
        mac_frame = ctk.CTkFrame(self.sidebar_frame)
        mac_frame.pack(pady=10, fill="x", padx=10)
        self.master_mac_lbl = ctk.CTkLabel(mac_frame, text="MAC Master:\nAguardando...", text_color="#00FFFF", font=("Consolas", 12))
        self.master_mac_lbl.pack(pady=5)
        self.emissor_mac_lbl = ctk.CTkLabel(mac_frame, text="MAC Emissor:\nNenhum pacote", text_color="#FFA500", font=("Consolas", 12))
        self.emissor_mac_lbl.pack(pady=5)

        self.port_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Porta COM (ex: COM4)")
        self.port_entry.pack(pady=10, padx=20, fill="x")

        # Senha com botão Show/Hide
        pwd_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        pwd_frame.pack(pady=5, padx=20, fill="x")
        self.pwd_entry = ctk.CTkEntry(pwd_frame, placeholder_text="Senha AES-GCM", show="*")
        self.pwd_entry.insert(0, "senha_utfpr_2026")
        self.pwd_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.show_pwd_btn = ctk.CTkButton(pwd_frame, text="👁", width=30, command=self.toggle_password)
        self.show_pwd_btn.pack(side="right")

        self.connect_btn = ctk.CTkButton(self.sidebar_frame, text="Conectar e Aguardar", command=self.toggle_connection, fg_color="#1F6AA5")
        self.connect_btn.pack(pady=20, padx=20, fill="x")
        
        self.status_lbl = ctk.CTkLabel(self.sidebar_frame, text="Status: Desconectado", text_color="gray")
        self.status_lbl.pack()

        # ================= ÁREA PRINCIPAL =================
        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.main_frame, text="Fluxo de Recepção", font=("Arial", 24, "bold")).pack(pady=10)

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

    def log(self, title, content):
        self.log_box.insert("end", f"=== {title} ===\n{content}\n\n")
        self.log_box.see("end")
        
    def limpar_tela(self):
        self.log_box.delete("1.0", "end")
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

    def toggle_connection(self):
        if not self.reading_serial:
            self.port = self.port_entry.get()
            if not self.port:
                self.log("ERRO", "Preencha a porta COM.")
                return
            
            self.reading_serial = True
            self.connect_btn.configure(text="Desconectar", fg_color="#DC143C", hover_color="#8B0000")
            self.status_lbl.configure(text="Escutando a porta...", text_color="#00FF00")
            self.limpar_tela()
            
            self.thread = threading.Thread(target=self.serial_loop, daemon=True)
            self.thread.start()
        else:
            self.reading_serial = False
            self.connect_btn.configure(text="Conectar e Aguardar", fg_color="#1F6AA5")
            self.status_lbl.configure(text="Status: Desconectado", text_color="gray")

    def serial_loop(self):
        try:
            with serial.Serial(self.port, 115200, timeout=1) as ser:
                while self.reading_serial:
                    if ser.in_waiting:
                        line = ser.readline().decode('ascii', errors='ignore').strip()
                        
                        if line.startswith("MASTER_MAC:"):
                            mac = line.split(":", 1)[1]
                            self.master_mac_lbl.configure(text=f"MAC Master:\n{mac}")
                            
                        elif "|" in line and line.count("|") >= 1:
                            sender_mac, chunk = line.split("|", 1)
                            self.emissor_mac_lbl.configure(text=f"MAC Emissor:\n{sender_mac}")
                            self.accumulated_data += chunk
                            
                            if "_END_" in self.accumulated_data:
                                payload = self.accumulated_data.replace("_END_", "")
                                self.accumulated_data = ""
                                self.after(0, self.processar_sinal_recebido, payload)
                                
        except Exception as e:
            self.after(0, self.log, "ERRO SERIAL", str(e))
            self.reading_serial = False
            self.connect_btn.configure(text="Conectar e Aguardar", fg_color="#1F6AA5")
            self.status_lbl.configure(text="Erro de Conexão", text_color="red")

    def processar_sinal_recebido(self, payload):
        self.limpar_tela()
        self.log("Notificação de Rede", "Sinal ESP-NOW completo recebido! Iniciando processamento...")
        try:
            # O protocolo agora tem 3 partes: ALGO | TEST_FLAG | SINAL
            algo, test_flag_str, signal_str = payload.split("|", 2)
            is_test = test_flag_str == "1"
            
            signal_list = [float(x) for x in signal_str.split(",")]
            signal_array = np.array(signal_list, dtype=np.float32)
            pwd = self.pwd_entry.get()
            
            self.log(f"1. Sinal Recebido ({algo})", str(signal_list[:50]) + ("..." if len(signal_list)>50 else ""))
            
            # Plot do Sinal Recebido
            samples_per_bit = 1 if algo == "NRZ" else 2
            fig_wave = plot_signal_waveform(signal_array, f"Forma de Onda Recebida ({algo})", samples_per_bit)
            canvas_wave = FigureCanvasTkAgg(fig_wave, master=self.graph_frame)
            canvas_wave.draw()
            canvas_wave.get_tk_widget().pack(fill="x", pady=5)

            # Decodificação da Linha
            binary_string = decode_line_code(signal_array, algo)
            self.log("2. Binário Recuperado", group_binary(binary_string))

            # Plot dos Bits
            fig_bits = plot_binary_signal(binary_string, "Bits Recuperados")
            canvas_bits = FigureCanvasTkAgg(fig_bits, master=self.graph_frame)
            canvas_bits.draw()
            canvas_bits.get_tk_widget().pack(fill="x", pady=5)

            if is_test:
                self.log("3. Fim do Processo (Modo Teste)", "A mensagem não possui criptografia ou conversão ASCII.")
                return

            # Reconstrução e Descriptografia
            encrypted_bytes = binary_to_bytes(binary_string)
            self.log("3. Mensagem Criptografada (AES-GCM)", f"Base64: {bytes_to_base64(encrypted_bytes)}\nHex: {encrypted_bytes.hex(' ')}")
            
            decrypted_bytes = decrypt_bytes(encrypted_bytes, pwd)
            original_message = bytes_to_text(decrypted_bytes)
            self.log("4. MENSAGEM ORIGINAL RECUPERADA", original_message)
            
        except Exception as e:
            self.log("ERRO DE PROCESSAMENTO", str(e))

if __name__ == "__main__":
    app = ReceptorApp()
    app.mainloop()