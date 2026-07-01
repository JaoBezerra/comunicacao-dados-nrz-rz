#include <esp_now.h>
#include <WiFi.h>

// SUBSTITUA PELO MAC DO MASTER (RECEPTOR)
// Exemplo: se for 24:0A:C4:XX:XX:XX, coloque {0x24, 0x0A, 0xC4, 0xXX, 0xXX, 0xXX}
uint8_t masterAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

void setup() {
    Serial.begin(115200);
    WiFi.mode(WIFI_STA);

    if (esp_now_init() != ESP_OK) {
        Serial.println("Erro ESP-NOW");
        return;
    }

    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, masterAddress, 6);
    peerInfo.channel = 0;
    peerInfo.encrypt = false;
    
    if (esp_now_add_peer(&peerInfo) != ESP_OK) {
        Serial.println("Falha ao adicionar peer");
        return;
    }
}

void loop() {
    // Lê os chunks (pedaços de sinal) enviados pelo Computador Transmissor
    if (Serial.available()) {
        String data = Serial.readStringUntil('\n');
        data.trim();
        
        if(data.length() > 0) {
            // O pacote é enviado imediatamente ao Master
            esp_now_send(masterAddress, (uint8_t *)data.c_str(), data.length());
            // Um leve delay para evitar congestionamento da rede e perda de pacotes
            delay(15); 
        }
    }
}