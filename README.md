# ⚡ Monitorização Inteligente de Energia: Xerém

Esta é uma aplicação interativa desenvolvida com [Streamlit](https://streamlit.io/) que demonstra a aplicação de uma arquitetura de dados moderna baseada em **Data-as-a-Service (DaaS)**. A aplicação consome um *Data Product* validado (`df_gold`) da camada Gold no Databricks, fornecendo aos utilizadores de negócio insights valiosos sobre o consumo de energia, temperatura e custos operacionais.

## 🚀 Funcionalidades Principais

- **Monitorização SRE e Qualidade de Dados:** Exibição em tempo real do status da pipeline (System Healthy / SLO Breach) baseada na auditoria da qualidade dos dados da camada Gold.
- **Filtros Dinâmicos:** Filtre os dados de energia por período (intervalo de datas) e por Bandeiras Tarifárias (Verde, Intermediária, Vermelha).
- **KPIs em Tempo Real:** 
  - Pico Máximo de Carga (MWmed)
  - Pico de Temperatura (°C)
  - Custo Médio Horário (BRL)
- **Visualização de Correlações:** Gráficos interativos (via Altair) ilustrando o impacto do aumento da temperatura no consumo de energia (efeito de refrigeração) e como as diferentes bandeiras tarifárias penalizam o custo em horários de ponta.

## 🛠️ Tecnologias Utilizadas

- **Frontend / App:** Python 3, Streamlit, Altair
- **Processamento de Dados:** Pandas
- **Integração na Cloud:** Conector Databricks SQL

## ⚙️ Configuração Local

Para correr a aplicação localmente, siga os passos abaixo:

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure os Segredos de Conexão:
Crie um ficheiro em `.streamlit/secrets.toml` com as suas credenciais do Databricks:
```toml
[databricks]
server_hostname = "seu_hostname_aqui"
http_path = "seu_http_path_aqui"
access_token = "seu_token_aqui"
```
*(Nota: O ficheiro `secrets.toml` está incluído no `.gitignore` para evitar fugas de dados confidenciais).*

3. Execute a Aplicação:
```bash
streamlit run app.py
```

## 📋 Arquitetura DaaS

A aplicação liga-se de forma desacoplada ao ambiente de Analytics. Em caso de falha temporária no sistema origem, existe um mecanismo de segurança que carrega dados de fallback locais (mock) para garantir a continuidade da experiência e evitar paragens na apresentação.
