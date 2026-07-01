#include <esp_now.h>
#include <WiFi.h>

void onReceive(const uint8_t *mac, const uint8_t *incomingData, int len) {
    char macStr[18];
    // Formata o MAC address do Emissor
    snprintf(macStr, sizeof(macStr), "%02x:%02x:%02x:%02x:%02x:%02x",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    
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
    WiFi.mode(WIFI_STA);
    
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