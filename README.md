# 🛰️ Localizador Expert (LocExpert)

> Sistema tático de monitoramento, geolocalização e gestão de dispositivos em tempo real com interface HUD e conformidade LGPD.

O **Localizador Expert** é uma aplicação web de alta performance desenvolvida em **Python** utilizando **Streamlit** e **Folium**, projetada para rastreamento de coordenadas GPS, leitura de telemetria de rede (IP e MAC Address), governança hierárquica (ADM Master e Clientes Gestores) e extração automatizada de relatórios operacionais.

---

## ✨ Recursos Principais

* **🗺️ Interface HUD Tática:** Design imersivo inspirado em centrais de comando, com temas escuros customizados, animações de radar e suporte a plano de fundo tático (`FundoTela.jpg`)[cite: 13, 14].
* **📍 Geolocalização em Tempo Real:** Integração com mapas interativos (Folium) para exibição precisa de coordenadas geográficas, endereços reversos (via Nominatim) e rotas.
* **🔒 Governança Hierárquica e LGPD:** 
  * Perfil **ADM Master**: Controle total, aprovação de cadastros, edição de perfis e visualização global.
  * Perfil **Cliente Gestor**: Gestão de subordinados e monitorados vinculados à sua conta.
  * Portal de Cadastro com termo de consentimento explícito em conformidade com a **Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018)**.
* **📊 Extração Avançada de Relatórios:** Exportação flexível de dados nos formatos **PDF** (via ReportLab), **Excel (`.xlsx`)** e **Texto (`.txt`)**, com filtros personalizados por período e amostragem.
* **⚙️ Telemetria de Hardware e Rede:** Captura automática de identificadores de rede (IP público e endereço MAC).

---

## 🚀 Como Executar o Projeto Localmente

### 1. Pré-requisitos
Certifique-se de ter o **Python 3.8+** instalado em sua máquina.

### 2. Clonar o Repositório
```bash
git clone [https://github.com/MarceloFons/Localizador.git](https://github.com/MarceloFons/Localizador.git)
cd Localizador