# Voyage Voyage

Aplicação web acadêmica de planejamento de viagens com dois agentes
colaborativos, desenvolvida com LangGraph e Groq.

A interface usa a imagem `assets/travel-background.jpg` como fundo visual,
inspirada na estética de colagem urbana da pasta de referências.

## Como executar

1. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

2. Copie `.env.example` para `.env` e informe sua chave gratuita da Groq,
   ou digite a chave diretamente na barra lateral da aplicação.

3. Abra a aplicação no navegador:

   ```bash
   streamlit run app.py
   ```

O terminal serve apenas para iniciar o servidor uma vez. Durante a demonstração,
a interação acontece pela página web.

## Publicação gratuita

A opção recomendada é o [Streamlit Community Cloud](https://share.streamlit.io/).
Conecte o repositório, selecione `app.py` e cadastre `GROQ_API_KEY` em
**App settings > Secrets**. O site publicado pode ser acessado sem login pelos
visitantes. A conta é necessária apenas para quem publica e administra o app.

Alternativas são o [Hugging Face Spaces](https://huggingface.co/spaces) e o
[Render](https://render.com/). Elas também podem publicar um app público sem
login para o visitante, mas possuem limites de uso e podem hibernar.

## Requisitos demonstrados

- **Agente Pesquisador:** interpreta o pedido, analisa o destino e solicita o
  cálculo de orçamento.
- **Agente Planejador:** recebe as mensagens anteriores e cria o roteiro por dia.
- **Ferramenta `@tool`:** `calcular_orcamento`, executada pelo fluxo do LangGraph
  através de `ToolNode`.
- **Framework:** LangGraph.
- **LLM:** Groq, usando o modelo de produção `openai/gpt-oss-120b`.
