import customtkinter as ctk
import serial
import threading
import numpy as np
from encoding_module import recover_message_from_signal

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class ReceptorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Host B - Receptor (Serial/ESP-NOW)")
        self.geometry("600x650")
        
        self.reading_serial = False
        self.accumulated_data = ""

        ctk.CTkLabel(self, text="Receptor NRZ/RZ", font=("Arial", 20, "bold")).pack(pady=10)

        # Campos de Informação MAC
        mac_frame = ctk.CTkFrame(self)
        mac_frame.pack(pady=10, fill="x", padx=20)
        
        self.master_mac_lbl = ctk.CTkLabel(mac_frame, text="MAC Master (Local): Aguardando conexão...", text_color="cyan")
        self.master_mac_lbl.pack()
        
        self.emissor_mac_lbl = ctk.CTkLabel(mac_frame, text="MAC Emissor (Remoto): Nenhuma recepção ainda", text_color="orange")
        self.emissor_mac_lbl.pack()

        # Configurações
        self.port_entry = ctk.CTkEntry(self, placeholder_text="Porta COM", width=200)
        self.port_entry.pack(pady=5)

        self.pwd_entry = ctk.CTkEntry(self, placeholder_text="Senha AES-GCM", show="*", width=200)
        self.pwd_entry.insert(0, "senha_utfpr_2026")
        self.pwd_entry.pack(pady=5)

        self.connect_btn = ctk.CTkButton(self, text="Conectar e Aguardar", command=self.toggle_connection)
        self.connect_btn.pack(pady=10)

        self.log_box = ctk.CTkTextbox(self, width=550, height=300)
        self.log_box.pack(pady=10)

    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def toggle_connection(self):
        if not self.reading_serial:
            self.port = self.port_entry.get()
            if not self.port:
                self.log("Preencha a porta COM.")
                return
            
            self.reading_serial = True
            self.connect_btn.configure(text="Desconectar", fg_color="red")
            self.log("Iniciando escuta na Serial...")
            
            self.thread = threading.Thread(target=self.serial_loop, daemon=True)
            self.thread.start()
        else:
            self.reading_serial = False
            self.connect_btn.configure(text="Conectar e Aguardar", fg_color=["#3B8ED0", "#1F6AA5"])
            self.log("Desconectado.")

    def serial_loop(self):
        try:
            with serial.Serial(self.port, 115200, timeout=1) as ser:
                while self.reading_serial:
                    if ser.in_waiting:
                        line = ser.readline().decode('ascii', errors='ignore').strip()
                        
                        if line.startswith("MASTER_MAC:"):
                            mac = line.split(":", 1)[1]
                            self.master_mac_lbl.configure(text=f"MAC Master (Local): {mac}")
                            self.log(f"Setup: Meu MAC é {mac}")
                            
                        elif "|" in line:
                            sender_mac, chunk = line.split("|", 1)
                            self.emissor_mac_lbl.configure(text=f"MAC Emissor (Remoto): {sender_mac}")
                            self.accumulated_data += chunk
                            
                            # Verifica se o sinal terminou
                            if "_END_" in self.accumulated_data:
                                payload = self.accumulated_data.replace("_END_", "")
                                self.accumulated_data = "" # Reseta para próxima mensagem
                                self.processar_sinal_recebido(payload)
                                
        except Exception as e:
            self.log(f"Erro na Serial: {e}")
            self.reading_serial = False
            self.connect_btn.configure(text="Conectar e Aguardar", fg_color=["#3B8ED0", "#1F6AA5"])

    def processar_sinal_recebido(self, payload):
        self.log("\nSinal completo recebido! Decodificando...")
        try:
            algo, signal_str = payload.split(":", 1)
            signal_list = [float(x) for x in signal_str.split(",")]
            signal_array = np.array(signal_list, dtype=np.float32)
            
            pwd = self.pwd_entry.get()
            
            # Chama o seu módulo original de criptografia e decodificação
            result = recover_message_from_signal(signal_array, algo, pwd)
            
            self.log(f"Algoritmo: {algo}")
            self.log(f"Binário Recuperado:\n{result['binary_string'][:50]}... (truncado)")
            self.log(f"MENSAGEM SECRETA: {result['original_message']}")
            self.log("-" * 40)
            
        except Exception as e:
            self.log(f"ERRO DE DECODIFICAÇÃO/AES: {e}")

if __name__ == "__main__":
    app = ReceptorApp()
    app.mainloop()