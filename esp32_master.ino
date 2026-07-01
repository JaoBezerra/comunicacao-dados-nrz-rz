#include <esp_now.h>
#include <WiFi.h>

// Nova assinatura exigida pelas versões 3.x.x do pacote ESP32
void onReceive(const esp_now_recv_info_t *esp_now_info, const uint8_t *incomingData, int len) {
    char macStr[18];
    
    // O MAC address agora fica dentro da estrutura esp_now_info no campo src_addr
    snprintf(macStr, sizeof(macStr), "%02x:%02x:%02x:%02x:%02x:%02x",
             esp_now_info->src_addr[0], esp_now_info->src_addr[1], 
             esp_now_info->src_addr[2], esp_now_info->src_addr[3], 
             esp_now_info->src_addr[4], esp_now_info->src_addr[5]);
    
    // Converte os dados recebidos para String
    String data = "";
    for (int i = 0; i < len; i++) {
        data += (char)incomingData[i];
    }
    
    // Envia para o Computador Receptor via Serial no formato MAC|DADOS
    Serial.print(macStr);
    Serial.print("|");
    Serial.println(data);
}

void setup() {
    Serial.begin(115200);
    
    // Define o modo Wi-Fi
    WiFi.mode(WIFI_STA);
    
    // Dá tempo ao hardware do rádio para inicializar e ler a memória interna
    delay(100); 
    
    // Imprime o próprio MAC na inicialização para o PC ler
    Serial.print("MASTER_MAC:");
    Serial.println(WiFi.macAddress());

    if (esp_now_init() != ESP_OK) {
        Serial.println("Erro ao inicializar ESP-NOW");
        return;
    }
    
    esp_now_register_recv_cb(onReceive);
}

void loop() {
    // A recepção ocorre de forma assíncrona na função onReceive
}