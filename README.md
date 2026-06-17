# Comunicação de Dados — Codificação de Linha NRZ/RZ

Projeto desenvolvido para a disciplina de **Comunicação de Dados**, com implementação de um sistema de transmissão entre dois hosts usando **codificação de linha NRZ/RZ**, **criptografia AES-GCM**, **conversão para binário usando ASCII estendido** e **comunicação em rede via socket TCP**.

O sistema possui dois lados:

* **Host A — Transmissor**
* **Host B — Receptor**

O Host A realiza o processo de envio da mensagem, enquanto o Host B realiza o processo inverso, reconstruindo a mensagem original a partir do sinal recebido.

---

## Objetivo do Projeto

Implementar uma aplicação desktop/web local capaz de simular uma transmissão digital completa, seguindo o fluxo:

```text
Mensagem original
↓
Criptografia AES-GCM
↓
Conversão para binário usando ASCII estendido
↓
Codificação de linha NRZ ou RZ
↓
Geração da forma de onda
↓
Envio pela rede
↓
Recepção no Host B
↓
Decodificação NRZ/RZ
↓
Reconstrução do binário
↓
Descriptografia AES-GCM
↓
Mensagem original recuperada
```

---

## Algoritmos Implementados

### NRZ Unipolar

No modo **NRZ**, cada bit é representado por um único nível de sinal:

```text
bit 1 -> +1
bit 0 ->  0
```

O sinal não retorna a zero no meio do intervalo de bit.

Exemplo:

```text
Bits:  01010010
NRZ:   0 +1 0 +1 0 0 +1 0
```

---

### RZ Polar

No modo **RZ**, cada bit é dividido em duas partes. O sinal retorna a zero dentro do próprio intervalo do bit:

```text
bit 1 -> +1, 0
bit 0 -> -1, 0
```

Exemplo:

```text
Bits:  01010010
RZ:    -1,0  +1,0  -1,0  +1,0  -1,0  -1,0  +1,0  -1,0
```

---

## Criptografia Utilizada

A criptografia utilizada é **AES-256-GCM**, implementada com a biblioteca `cryptography`.

O processo usa:

* **AES-GCM** para criptografia simétrica autenticada;
* **PBKDF2-HMAC-SHA256** para derivar a chave a partir de uma senha;
* **salt aleatório** para tornar a chave derivada diferente a cada execução;
* **nonce aleatório** para garantir que o mesmo texto gere saídas criptografadas diferentes;
* **tag de autenticação** para detectar senha incorreta ou alteração nos dados.

O pacote criptografado possui a estrutura:

```text
salt + nonce + ciphertext + tag
```

Esse pacote é convertido para binário e depois codificado em NRZ ou RZ.

---

## Conversão para Binário

A mensagem é convertida para bytes usando a codificação **Latin-1**, que permite representar caracteres acentuados comuns em português usando 8 bits.

Exemplo:

```text
Mensagem: Olá UTFPR - João
```

Após a criptografia, cada byte do pacote criptografado é convertido para binário com 8 bits:

```text
01010010 01101111 11100100 ...
```

---

## Funcionalidades

### Host A — Transmissor

O transmissor permite:

* digitar a mensagem original;
* escolher o algoritmo de codificação de linha: `NRZ` ou `RZ`;
* definir a senha usada no AES-GCM;
* visualizar o pacote criptografado em Base64 e hexadecimal;
* visualizar a sequência binária;
* visualizar a sequência de níveis do sinal;
* gerar o gráfico da forma de onda;
* enviar o sinal codificado para o Host B via rede.

---

### Host B — Receptor

O receptor permite:

* aguardar conexão em uma porta TCP;
* selecionar a interface de escuta;
* receber o sinal enviado pelo Host A;
* exibir a forma de onda recebida;
* aplicar o processo inverso da codificação NRZ/RZ;
* reconstruir a sequência binária;
* recuperar o pacote criptografado;
* descriptografar usando AES-GCM;
* exibir a mensagem original recuperada.

---

## Estrutura do Projeto

```text
comunicacao-dados-nrz-rz/
├── host.py                  # Interface do Host A — transmissor
├── receptor.py              # Interface do Host B — receptor
├── encoding_module.py       # Codificação, decodificação, criptografia e conversão binária
├── visualization.py         # Geração dos gráficos das formas de onda
├── requirements.txt         # Dependências do projeto
├── .gitignore               # Arquivos ignorados pelo Git
├── normas do trabalho.pdf   # Documento com as especificações do trabalho
└── README.md                # Documentação do projeto
```

---

## Tecnologias Utilizadas

* Python
* Streamlit
* NumPy
* Matplotlib
* Cryptography
* Socket TCP
* JSON

---

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/SEU_USUARIO/comunicacao-dados-nrz-rz.git
cd comunicacao-dados-nrz-rz
```

---

### 2. Criar ambiente virtual

No Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

Caso ainda não exista o arquivo `requirements.txt`, instale manualmente:

```bash
pip install streamlit matplotlib numpy cryptography
pip freeze > requirements.txt
```

---

## Execução Local para Teste

O teste local usa `127.0.0.1` e serve apenas para desenvolvimento.

### Terminal 1 — iniciar o receptor

```powershell
streamlit run receptor.py --server.port 8501
```

### Terminal 2 — iniciar o transmissor

```powershell
streamlit run host.py --server.port 8502
```

No navegador:

```text
Host B: http://localhost:8501
Host A: http://localhost:8502
```

Configuração para teste local:

```text
Host B:
Interface de escuta: 0.0.0.0
Porta: 65432
Senha AES-GCM: senha_utfpr_2026

Host A:
IP do Host B: 127.0.0.1
Porta: 65432
Senha AES-GCM: senha_utfpr_2026
```

---

## Execução entre Dois Computadores

Para a apresentação, a comunicação deve ser feita entre dois computadores reais na mesma rede.

### Computador B — Receptor

```powershell
streamlit run receptor.py --server.address 0.0.0.0 --server.port 8501
```

No Host B, configure:

```text
Interface de escuta: 0.0.0.0
Porta: 65432
Senha AES-GCM: senha_utfpr_2026
```

O próprio receptor exibirá o IP principal do computador, por exemplo:

```text
192.168.0.25
```

---

### Computador A — Transmissor

```powershell
streamlit run host.py --server.address 0.0.0.0 --server.port 8502
```

No Host A, configure:

```text
IP do Host B: 192.168.0.25
Porta: 65432
Senha AES-GCM: senha_utfpr_2026
```

A senha usada no Host A e no Host B deve ser a mesma.

---

## Campo “Interface de escuta”

No Host B, o campo **Interface de escuta** define em qual endereço de rede o receptor aguardará conexões.

Opções comuns:

```text
0.0.0.0
```

Escuta em todas as interfaces de rede disponíveis. É a opção recomendada para teste entre dois computadores.

```text
192.168.x.x
```

Escuta apenas em uma interface específica da rede local.

```text
127.0.0.1
```

Escuta apenas no próprio computador. Serve para teste local, mas não para a apresentação em rede real.

---

## Modo de Teste sem Criptografia

O Host A possui um modo de teste sem criptografia. Esse modo permite inserir diretamente uma sequência binária para validar apenas a codificação de linha.

Exemplo:

```text
1100001000000000
```

Nesse modo, o fluxo é:

```text
Sequência binária
↓
NRZ ou RZ
↓
Gráfico
↓
Envio
↓
Recepção
↓
Decodificação
↓
Binário recuperado
```

Esse modo é útil para validar o algoritmo de codificação antes de aplicar a criptografia.

---

## Testes Recomendados

### Teste 1 — NRZ com mensagem

Mensagem:

```text
Olá UTFPR - João
```

Resultado esperado:

```text
Mensagem recuperada no Host B: Olá UTFPR - João
```

---

### Teste 2 — RZ com mensagem

Mensagem:

```text
Olá UTFPR - João
```

Resultado esperado:

```text
Mensagem recuperada no Host B: Olá UTFPR - João
```

---

### Teste 3 — Senha incorreta

Use uma senha no Host A e outra senha diferente no Host B.

Resultado esperado:

```text
Falha na descriptografia. A senha está incorreta ou os dados foram alterados.
```

---

### Teste 4 — Sequência binária sem criptografia

Ative o modo de teste no Host A e envie uma sequência binária.

Resultado esperado:

```text
O Host B deve recuperar a mesma sequência binária enviada.
```

---

## Possíveis Problemas e Soluções

### Erro: Connection refused

Possíveis causas:

* O Host B não está aguardando mensagem;
* IP incorreto no Host A;
* porta incorreta;
* firewall bloqueando a conexão.

Solução:

* iniciar primeiro o Host B;
* clicar em “Aguardar mensagem”;
* conferir o IP mostrado no Host B;
* conferir a porta;
* liberar a porta no firewall.

---

### Erro: Address already in use

A porta já está ocupada.

Solução:

* trocar a porta de comunicação, por exemplo de `65432` para `65433`;
* ou encerrar o processo que está usando a porta.

---

### Erro de descriptografia

Possíveis causas:

* senha diferente entre Host A e Host B;
* dados alterados durante o processo;
* algoritmo incorreto selecionado.

Solução:

* usar a mesma senha nos dois hosts;
* reenviar a mensagem;
* verificar se o algoritmo recebido é o mesmo enviado.

---

## Liberação de Firewall no Windows

Caso a comunicação entre computadores não funcione, execute no PowerShell como administrador:

```powershell
netsh advfirewall firewall add rule name="ComDadosPython65432" dir=in action=allow protocol=TCP localport=65432
```

Também pode ser necessário permitir o Python no Firewall do Windows.

---

## Observação sobre Autoria

Este projeto foi desenvolvido com base autorizada em uma implementação anterior de um colega da disciplina, sendo adaptado para os algoritmos **NRZ** e **RZ**, com reestruturação da codificação de linha, criptografia AES-GCM, conversão binária e processo completo de transmissão e recepção.

---

## Resumo do Fluxo Implementado

```text
Host A:
Mensagem original
→ Latin-1
→ AES-GCM
→ Binário
→ NRZ/RZ
→ Gráfico
→ Socket TCP

Host B:
Socket TCP
→ Gráfico
→ NRZ/RZ inverso
→ Binário
→ AES-GCM inverso
→ Mensagem original
```

---

## Status

Implementado:

* interface gráfica com Streamlit;
* codificação NRZ;
* codificação RZ;
* decodificação NRZ;
* decodificação RZ;
* criptografia AES-256-GCM;
* conversão para binário em 8 bits;
* suporte a caracteres acentuados via Latin-1;
* envio e recepção via socket TCP;
* gráficos das formas de onda no transmissor e no receptor;
* modo de teste sem criptografia.

---

**Projeto desenvolvido para a disciplina de Comunicação de Dados.**
