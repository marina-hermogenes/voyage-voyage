from __future__ import annotations

import os
import re
from html import escape
from base64 import b64encode
from pathlib import Path
from typing import Annotated, TypedDict

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


load_dotenv()


class TravelState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


@tool
def calcular_orcamento(
    quantidade_dias: int,
    custo_diario: float,
    quantidade_pessoas: int,
) -> str:
    """Calcula o custo estimado da viagem em reais."""
    if quantidade_dias <= 0 or quantidade_pessoas <= 0 or custo_diario < 0:
        raise ValueError("Os valores de dias, pessoas e custo devem ser válidos.")
    total = quantidade_dias * custo_diario * quantidade_pessoas
    return (
        f"Estimativa calculada: R$ {total:,.2f} "
        f"para {quantidade_pessoas} pessoa(s) durante {quantidade_dias} dia(s)."
    ).replace(",", "X").replace(".", ",").replace("X", ".")


TOOLS = [calcular_orcamento]


def construir_grafo(model: ChatGroq):
    researcher = model.bind_tools(TOOLS)

    def pesquisar(state: TravelState) -> dict[str, list[BaseMessage]]:
        response = researcher.invoke(
            [
                SystemMessage(
                    content=(
                        "Você é o Agente Pesquisador de Viagens. Analise os dados "
                        "fornecidos, estime o orçamento usando a ferramenta disponível "
                        "e reúna recomendações práticas para o destino. "
                        "Sempre use a ferramenta de orçamento antes de responder."
                    )
                ),
                *state["messages"],
            ]
        )
        return {"messages": [response]}

    planner = model

    def planejar(state: TravelState) -> dict[str, list[BaseMessage]]:
        response = planner.invoke(
            [
                SystemMessage(
                    content=(
                        "Você é o Agente Planejador. Use a análise do pesquisador "
                        "e produza um roteiro claro em português, separado por dias. "
                        "Respeite duração, orçamento, interesses e estilo informados. "
                        "Inclua observações sobre custos, deslocamento e limitações. "
                        "Não invente preços exatos nem reservas."
                    )
                ),
                *state["messages"],
            ]
        )
        return {"messages": [response]}

    graph = StateGraph(TravelState)
    graph.add_node("pesquisador", pesquisar)
    graph.add_node("ferramenta_orcamento", ToolNode(TOOLS))
    graph.add_node("planejador", planejar)
    graph.add_edge(START, "pesquisador")
    graph.add_conditional_edges(
        "pesquisador",
        tools_condition,
        {"tools": "ferramenta_orcamento", END: "planejador"},
    )
    graph.add_edge("ferramenta_orcamento", "planejador")
    graph.add_edge("planejador", END)
    return graph.compile()


def renderizar_cabecalho() -> None:
    favicon_path = Path(__file__).parent / "assets" / "favicon-jpeg11"
    st.set_page_config(
        page_title="Voyage Voyage | Planejador inteligente",
        page_icon=str(favicon_path) if favicon_path.exists() else "✈️",
        layout="wide",
    )
    background_path = Path(__file__).parent / "assets" / "travel-background.jpg"
    robloxx_path = Path(__file__).parent / "assets" / "robloxx.jpeg"
    taxi_path = Path(__file__).parent / "assets" / "taxi.png"
    background_uri = ""
    robloxx_uri = ""
    taxi_uri = ""
    if background_path.exists():
        encoded_image = b64encode(background_path.read_bytes()).decode("ascii")
        background_uri = f"data:image/jpeg;base64,{encoded_image}"
    if robloxx_path.exists():
        encoded_robloxx = b64encode(robloxx_path.read_bytes()).decode("ascii")
        robloxx_uri = f"data:image/jpeg;base64,{encoded_robloxx}"
    if taxi_path.exists():
        encoded_taxi = b64encode(taxi_path.read_bytes()).decode("ascii")
        taxi_uri = f"data:image/png;base64,{encoded_taxi}"

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Bungee&family=DM+Sans:wght@400;500;700&family=Space+Mono:wght@400;700&display=swap');
        :root { color-scheme: light; --black: #111111; --pink: #f900a8; --yellow: #eaff00; --blue: #4c5cff; --green: #b7ff3c; --paper: #fff8ed; }
        html, body, [data-testid="stAppViewContainer"] { color-scheme: light !important; }
        .stApp { background-color: var(--paper); color: var(--black); position: relative; }
        .stApp::before { background-image: linear-gradient(90deg, rgba(255, 248, 237, .88), rgba(255, 248, 237, .36)),
                         url('__BACKGROUND_URI__'); background-position: center; background-size: cover;
                         background-attachment: fixed; content: ''; inset: 0; opacity: .92; pointer-events: none;
                         position: fixed; transform: scaleX(-1); z-index: 0; }
        [data-testid="stAppViewContainer"] { position: relative; z-index: 1; }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] { background: var(--black); border-right: 5px solid var(--pink); }
        [data-testid="stSidebar"] * { color: white !important; }
        [data-testid="stSidebar"] input {
            background: #2b2b2b !important;
            border: 2px solid var(--yellow) !important;
            color: white !important;
            caret-color: var(--yellow) !important;
        }
        [data-testid="stSidebar"] input::placeholder { color: #cfcfcf !important; opacity: 1; }
        [data-testid="stSidebar"] [data-baseweb="input"] { background: #2b2b2b !important; }
        h1, h2, h3, button { font-family: 'Bungee', sans-serif !important; }
        label, p, div, input, textarea, select { font-family: 'DM Sans', sans-serif; }
        h1 { color: var(--black); font-size: 4.3rem !important; line-height: .95 !important;
             letter-spacing: -.04em; margin: 0; text-transform: uppercase; }
        .hero-wrap { background: var(--pink); border: 5px solid var(--black); box-shadow: 12px 12px 0 var(--black);
                     margin: .5rem 0 2rem; padding: 2.2rem 2.4rem 1.7rem; position: relative;
                     transform: rotate(-1deg); }
        .hero-kicker { align-items: center; background: var(--yellow); border: 3px solid var(--black); display: inline-flex;
                       font-family: 'Space Mono', monospace; font-size: .78rem; font-weight: 700;
                       letter-spacing: .08em; margin-bottom: 1rem; padding: .4rem .7rem; }
        .hero-kicker img { border: 2px solid var(--black); height: 30px; margin: 0 .45rem;
                           object-fit: cover; transform: rotate(-7deg); width: 30px; }
        .hero-copy { font-size: 1.05rem; font-weight: 700; max-width: 650px; }
        .hero-taxi { bottom: 0; filter: drop-shadow(9px 9px 0 var(--black));
                     height: auto; object-fit: contain; position: absolute; right: 0;
                     transform: rotate(-1deg); transform-origin: bottom right;
                     width: 360px; z-index: 1; }
        .burst { color: var(--yellow); font-size: 5rem; line-height: 1; position: absolute; right: 2rem; top: 1rem; transform: rotate(15deg); }
        .agent-pill { background: var(--yellow); border: 3px solid var(--black); color: var(--black);
                      display: inline-block; font-family: 'Space Mono', monospace; font-size: .77rem;
                      font-weight: 700; margin: .3rem .2rem 0 0; padding: .45rem .7rem; transform: rotate(2deg); }
        [data-testid="stForm"] { background: var(--black); border: 5px solid var(--green);
                                 box-shadow: 9px 9px 0 var(--pink); padding: 1.6rem 1.7rem 1.35rem;
                                 transform: none; }
        [data-testid="stForm"] label { color: white !important; font-family: 'Space Mono', monospace;
                                       font-size: .72rem; font-weight: 700; letter-spacing: .02em; }
        [data-testid="stForm"] input, [data-testid="stForm"] textarea,
        [data-testid="stForm"] [data-baseweb="select"] {
            background: white !important; border: 2px solid #b8b8b8 !important;
            border-radius: 12px !important; box-shadow: 3px 3px 0 rgba(17,17,17,.35);
            color: var(--black) !important; font-family: 'DM Sans', sans-serif !important;
            font-size: .9rem !important;
        }
        [data-testid="stForm"] [data-baseweb="select"] > div {
            background: white !important; border: 0 !important; border-radius: 9px !important;
            color: var(--black) !important; min-height: 42px;
        }
        [data-testid="stForm"] [data-baseweb="select"] div,
        [data-testid="stForm"] [data-baseweb="select"] span {
            color: var(--black) !important;
        }
        [data-testid="stForm"] [data-baseweb="select"] svg { fill: var(--black) !important; }
        [data-testid="stForm"] [data-baseweb="input"] {
            background: white !important; border: 2px solid #b8b8b8 !important;
            border-radius: 12px !important; box-shadow: 3px 3px 0 rgba(17,17,17,.35);
        }
        [data-testid="stForm"] [data-baseweb="input"] > div {
            background: white !important; border: 0 !important; border-radius: 9px !important;
        }
        [data-testid="stForm"] [data-baseweb="input"] input {
            background: transparent !important; border: 0 !important; box-shadow: none !important;
        }
        [data-testid="stForm"] textarea { min-height: 92px; padding-top: .7rem; }
        [data-testid="stForm"] input:focus,
        [data-testid="stForm"] textarea:focus,
        [data-testid="stForm"] [data-baseweb="select"]:focus-within {
            border-color: #777 !important; box-shadow: 3px 3px 0 rgba(17,17,17,.35);
            outline: none;
        }
        [data-testid="stForm"] [data-testid="stNumberInput"] button {
            background: #eeeeee !important; border: 0 !important; border-radius: 0 !important;
            color: var(--black) !important; min-height: 42px;
        }
        [data-testid="stForm"] [data-testid="stNumberInput"] > div {
            border-radius: 12px; overflow: visible;
        }
        [data-testid="stForm"] [data-testid="stFormSubmitButton"] { margin-top: .35rem; }
        .route-heading { background: linear-gradient(90deg, rgba(17,17,17,.96), rgba(17,17,17,.68)),
                         url('__BACKGROUND_URI__') center 42% / cover; color: white; border: 5px solid var(--black);
                         box-shadow: 8px 8px 0 var(--yellow); margin: 2.5rem 0 1.2rem;
                         min-height: 170px; padding: 1.1rem 1.4rem; position: relative; transform: rotate(-.6deg); }
        .route-heading h2 { color: var(--yellow); font-size: 2rem; margin: .5rem 0 .2rem; }
        .route-heading p { margin: 0; }
        .trip-table-wrap { background: white; border: 5px solid var(--black);
                           box-shadow: 9px 9px 0 var(--pink); margin: 2.5rem 0 1.4rem;
                           padding: 1.1rem; transform: rotate(.35deg); }
        .table-title { align-items: center; background: var(--black); color: white;
                       display: flex; gap: .8rem; justify-content: space-between;
                       margin: -.1rem -.1rem 1rem; padding: .8rem 1rem; }
        .table-title h2 { color: var(--yellow); font-size: 1.7rem; margin: 0; }
        .trip-table-scroll { overflow-x: auto; }
        .trip-table { border-collapse: separate; border-spacing: 0; min-width: 620px;
                      width: 100%; }
        .trip-table th { background: var(--pink); border-bottom: 4px solid var(--black);
                         color: white; font-family: 'Space Mono', monospace; font-size: .78rem;
                         padding: .85rem .75rem; text-align: left; text-transform: uppercase; }
        .trip-table th:first-child { width: 84px; }
        .trip-table td { border-bottom: 3px solid var(--black); color: var(--black);
                         font-family: 'Space Mono', monospace; font-size: .8rem;
                         font-weight: 700; line-height: 1.5; padding: .9rem .75rem; }
        .trip-table tbody tr:nth-child(odd) td { background: var(--yellow); }
        .trip-table tbody tr:nth-child(even) td { background: #b7ff3c; }
        .trip-table tbody tr:last-child td { border-bottom: 0; }
        .trip-table td:first-child { font-family: 'Bungee', sans-serif; font-size: 1.05rem;
                                     text-align: center; white-space: nowrap; }
        .route-sticker { background: var(--pink); border: 2px solid white; color: white;
                         font-family: 'Space Mono', monospace; font-size: .72rem; font-weight: 700;
                         padding: .35rem .55rem; }
        .route-collage { position: absolute; right: 1.25rem; top: -.9rem; }
        .route-collage img { filter: drop-shadow(7px 7px 0 var(--yellow)); height: 205px;
                             object-fit: contain; transform: rotate(8deg); width: 165px; }
        .route-collage img:nth-child(n+2) { display: none; }
        .day-card { border: 5px solid var(--black); display: block;
                    margin: 1.1rem 0; min-height: 0; box-shadow: 7px 7px 0 var(--black); }
        .day-0 { background: #ffdf3f; }
        .day-1 { background: #ff7eb6; }
        .day-2 { background: #71e6ff; }
        .day-3 { background: #b7ff3c; }
        .day-content { padding: 1.25rem 1.45rem 1.35rem; }
        .day-art { bottom: .6rem; filter: drop-shadow(5px 5px 0 var(--black)); height: 108px;
                   object-fit: contain; position: absolute; right: 1rem; transform: rotate(5deg); width: 150px; }
        .day-card { position: relative; }
        .day-card .day-content { padding-right: 7rem; }
        .day-content h3 { color: var(--black); font-size: 1.45rem; margin: .25rem 0 .65rem; }
        .day-content p, .day-content li { font-family: 'Space Mono', monospace; font-size: .82rem; line-height: 1.65; }
        .day-content p { margin: .35rem 0; }
        .day-content ul { list-style: none; margin: .4rem 0; padding: 0; }
        .day-content li { margin: .35rem 0; }
        .day-label { font-family: 'Space Mono', monospace; font-size: .68rem; font-weight: 700; letter-spacing: .12em; }
        .bullet { font-weight: 700; margin-right: .35rem; }
        .stButton > button { background: var(--black); border: 3px solid var(--black); border-radius: 0;
                             box-shadow: 5px 5px 0 var(--pink); color: white; font-family: 'Bungee', sans-serif;
                             padding: .7rem 1.4rem; text-transform: uppercase; }
        .stButton > button:hover { background: var(--blue); border-color: var(--black); color: white; }
        [data-testid="stAlert"] { background: #fff8ed !important; border: 3px solid var(--black);
                                  border-radius: 0; color: var(--black) !important; }
        [data-testid="stAlert"] * { color: var(--black) !important; }
        [data-testid="stStatusWidget"] { background: var(--black) !important; border: 3px solid var(--black);
                                          color: white !important; }
        [data-testid="stStatusWidget"] * { color: white !important; }
        [data-testid="stAlert"][kind="success"] { background: var(--yellow) !important; color: var(--black) !important; }
        </style>
        <div class="hero-wrap">
        <div class="hero-kicker">VOYAGE VOYAGE <img src="__ROBLOXX_URI__" alt="Imagem decorativa"> ROTEIROS FORA DO ÓBVIO</div>
        <h1>Viaje<br>sem manual.</h1>
        <p class="hero-copy">Dois agentes colaboram para pesquisar o destino, calcular
        o orçamento e transformar suas ideias em um roteiro possível — do seu jeito.</p>
        <span class="agent-pill">◌ Agente pesquisador</span>
        <span class="agent-pill">✦ Agente planejador</span>
        <img class="hero-taxi" src="__TAXI_URI__" alt="Táxi">
        </div>
        """.replace("__BACKGROUND_URI__", background_uri)
        .replace("__ROBLOXX_URI__", robloxx_uri)
        .replace("__TAXI_URI__", taxi_uri)
    , unsafe_allow_html=True)


def obter_chave_api() -> str:
    try:
        secret_key = st.secrets.get("GROQ_API_KEY", "")
    except FileNotFoundError:
        secret_key = ""
    return str(secret_key or os.getenv("GROQ_API_KEY", ""))


def _separar_linha_tabela(line: str, delimiter: str | None) -> list[str]:
    if delimiter == "|":
        return [cell.strip() for cell in line.strip().strip("|").split("|")]
    if delimiter == "\t":
        return [cell.strip() for cell in line.split("\t")]
    return []


def _formatar_celula_tabela(cell: str) -> str:
    clean_cell = re.sub(r"<br\s*/?>", " · ", cell, flags=re.IGNORECASE)
    clean_cell = re.sub(r"</?p>", "", clean_cell, flags=re.IGNORECASE)
    formatted = escape(re.sub(r"^#+\s*", "", clean_cell).strip())
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", formatted)


def _rotulo_tabela(
    header_cells: list[str], table_number: int, day_number: int
) -> tuple[str, str, int]:
    normalized = [
        re.sub(r"[^a-záéíóúãõç ]", "", re.sub(r"^#+\s*", "", cell).lower())
        for cell in header_cells
    ]
    header_text = " ".join(normalized)
    if (
        "horário" in normalized[0]
        or "horario" in normalized[0]
        or "plano do dia" in normalized[0]
    ):
        day_number += 1
        return f"✦ DIA {day_number:02d}", f"Plano do dia {day_number}", day_number
    if "item" in normalized[0] or (
        "custo" in header_text and "atividade" not in header_text
    ):
        return "✦ ORÇAMENTO", "Custos estimados", day_number
    if normalized[0] == "dia" and any(
        word in header_text for word in ("principais atividades", "gastos", "gasto")
    ):
        return "✦ RESUMO", "Resumo da viagem", day_number
    if normalized[0] == "dia" and any(
        word in header_text for word in ("manhã", "manha", "tarde", "noite")
    ):
        return "✦ RESUMO", "Resumo da viagem", day_number
    return "✦ ROTEIRO", "Detalhes do roteiro", day_number


def renderizar_roteiro(content: str) -> None:
    """Render the planner response as colorful, readable day cards."""
    lines = [line.rstrip() for line in content.splitlines()]
    table_blocks: list[tuple[list[str], list[list[str]]]] = []
    index = 0
    while index < len(lines) - 1:
        header = lines[index].strip()
        separator = lines[index + 1].strip()
        if not header or not separator:
            index += 1
            continue
        delimiter = "|" if "|" in header else "\t" if "\t" in header else None
        header_cells = _separar_linha_tabela(header, delimiter)
        separator_cells = _separar_linha_tabela(separator, delimiter)
        is_separator = (
            delimiter is not None
            and len(separator_cells) == len(header_cells)
            and all(re.fullmatch(r"[:\-\s]+", cell) for cell in separator_cells)
        )
        if not is_separator:
            if delimiter == "\t" and len(header_cells) >= 2:
                rows: list[list[str]] = []
                index += 1
                while index < len(lines):
                    row = lines[index].strip()
                    if not row or "\t" not in row:
                        break
                    cells = _separar_linha_tabela(row, delimiter)
                    if len(cells) != len(header_cells):
                        break
                    rows.append(cells)
                    index += 1
                if rows:
                    table_blocks.append((header_cells, rows))
                    continue
            index += 1
            continue
        rows: list[list[str]] = []
        index += 2
        while index < len(lines):
            row = lines[index].strip()
            if not row or (delimiter == "|" and "|" not in row) or (
                delimiter == "\t" and "\t" not in row
            ):
                break
            cells = _separar_linha_tabela(row, delimiter)
            if len(cells) != len(header_cells):
                break
            rows.append(cells)
            index += 1
        if rows:
            table_blocks.append((header_cells, rows))
        if index < len(lines) and not lines[index].strip():
            index += 1
        continue

    if table_blocks:
        day_number = 0
        for table_number, (header_cells, data_rows) in enumerate(table_blocks, start=1):
            normalized_headers = [
                re.sub(r"[^a-záéíóúãõç ]", "", cell.lower()).strip()
                for cell in header_cells
            ]
            is_schedule = normalized_headers and (
                normalized_headers[0] in {"horário", "horario"}
            )
            if is_schedule and data_rows:
                current_period = ""
                normalized_rows = []
                for row in data_rows:
                    row = list(row)
                    if row[0].strip():
                        current_period = row[0].strip()
                    elif current_period:
                        row[0] = current_period
                    normalized_rows.append(row)
                data_rows = normalized_rows
            header_html = "".join(
                f"<th>{_formatar_celula_tabela(cell)}</th>" for cell in header_cells
            )
            rows_html = "".join(
                "<tr>"
                + "".join(f"<td>{_formatar_celula_tabela(cell)}</td>" for cell in row)
                + "</tr>"
                for row in data_rows
            )
            sticker, title, day_number = _rotulo_tabela(
                header_cells, table_number, day_number
            )
            clean_title = escape(re.sub(r"^#+\s*", "", title).strip())
            st.markdown(
                f"""
                <section class="trip-table-wrap">
                  <div class="table-title">
                    <span class="route-sticker">{sticker}</span>
                    <h2>{clean_title}</h2>
                  </div>
                  <div class="trip-table-scroll">
                    <table class="trip-table">
                      <thead><tr>{header_html}</tr></thead>
                      <tbody>{rows_html}</tbody>
                    </table>
                  </div>
                </section>
                """,
                unsafe_allow_html=True,
            )
        return

    sections = re.split(r"(?im)^(?=\s*#{0,3}\s*(?:dia|day)\s+\d+\b)", content)
    sections = [section.strip() for section in sections if section.strip()]
    if not sections:
        sections = [content.strip()]

    collage_paths = [Path(__file__).parent / "assets" / "route-camera.png"]
    collage_html = ""
    for path in collage_paths:
        if path.exists():
            encoded_image = b64encode(path.read_bytes()).decode("ascii")
            collage_html += (
                f'<img src="data:image/png;base64,{encoded_image}" '
                'alt="Referência visual de viagem">'
            )

    st.markdown(
        f"""
        <div class="route-heading">
          <span class="route-sticker">✦ ROTEIRO NA MÃO</span>
          <h2>Seu mapa de rolês</h2>
          <p>Um plano criado em colaboração pelo pesquisador e pelo planejador.</p>
          <div class="route-collage">{collage_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for index, section in enumerate(sections):
        lines = section.splitlines()
        title = lines[0].lstrip("# ").strip() if lines else f"Dia {index + 1}"
        if not re.match(r"(?i)(dia|day)\s+\d+", title):
            title = f"Dia {index + 1} · {title}"
        body_lines = lines[1:] if len(lines) > 1 else lines
        body_html_parts = []
        list_items = []
        for line in body_lines:
            clean_line = line.strip()
            if not clean_line or re.fullmatch(r"[-*_]{3,}", clean_line):
                continue
            clean_line = re.sub(r"^#+\s*", "", clean_line)
            clean_line = re.sub(r"^[\-*•]\s*", "", clean_line)
            clean_line = re.sub(r"^\d+[.)]\s*", "", clean_line)
            clean_line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escape(clean_line))
            if line.strip().startswith(("-", "*", "•")) or re.match(r"^\d+[.)]", line.strip()):
                list_items.append(f"<li><span class='bullet'>✦</span>{clean_line}</li>")
            else:
                if list_items:
                    body_html_parts.append("<ul>" + "".join(list_items) + "</ul>")
                    list_items = []
                body_html_parts.append(f"<p>{clean_line}</p>")
        if list_items:
            body_html_parts.append("<ul>" + "".join(list_items) + "</ul>")
        body_html = "".join(body_html_parts) or "<p>Roteiro personalizado para este dia.</p>"
        art_path = Path(__file__).parent / "assets" / f"route-sticker-{index + 11}.png"
        art_html = ""
        if art_path.exists() and index < 3:
            art_data = b64encode(art_path.read_bytes()).decode("ascii")
            art_html = (
                f'<img class="day-art" src="data:image/png;base64,{art_data}" '
                'alt="Colagem decorativa do dia">'
            )
        st.markdown(
            f"""
            <article class="day-card day-{index % 4}">
              {art_html}
              <div class="day-content">
                <div class="day-label">DIA {index + 1} · PARADA {index + 1}</div>
                <h3>{escape(title)}</h3>
                {body_html}
              </div>
            </article>
            """,
            unsafe_allow_html=True,
        )


def principal() -> None:
    renderizar_cabecalho()

    with st.sidebar:
        st.header("Como funciona")
        api_key = obter_chave_api()
        if api_key:
            st.success("Conexão com o modelo configurada.")
        else:
            api_key = st.text_input(
                "Chave Groq (modo local)",
                type="password",
                help="No deploy, configure GROQ_API_KEY nos Secrets da plataforma.",
            )
        model_name = st.selectbox(
            "Modelo",
            ["openai/gpt-oss-120b"],
            index=0,
        )
        st.divider()
        st.caption("Fluxo dos agentes")
        st.markdown("**01 · Pesquisador**  \nAnalisa o destino e usa a ferramenta.")
        st.markdown("**02 · Planejador**  \nTransforma a análise em roteiro.")

    with st.form("travel_form"):
        left, right = st.columns(2)
        with left:
            origem = st.text_input("Cidade de origem", "São Paulo")
            destino = st.text_input("Destino", "Rio de Janeiro")
            dias = st.number_input("Quantidade de dias", min_value=1, max_value=30, value=4)
            pessoas = st.number_input(
                "Quantidade de pessoas", min_value=1, max_value=20, value=2
            )
        with right:
            orcamento_diario = st.number_input(
                "Orçamento diário por pessoa (R$)",
                min_value=0.0,
                value=250.0,
                step=50.0,
            )
            estilo = st.selectbox(
                "Estilo da viagem",
                ["Econômica", "Equilibrada", "Confortável", "Aventura"],
            )
            interesses = st.text_area(
                "Interesses",
                "praias, cultura, gastronomia e passeios ao ar livre",
            )
        submitted = st.form_submit_button("Planejar minha viagem", type="primary")

    if not submitted:
        st.info("Preencha os dados para revelar seu roteiro.")
        return

    if not api_key:
        st.error(
            "Informe uma chave Groq na barra lateral. Ela é gratuita e necessária "
            "para executar os agentes."
        )
        return

    request = (
        f"Planeje uma viagem de {origem} para {destino}, com {dias} dias e "
        f"{pessoas} pessoa(s). O orçamento diário por pessoa é R$ {orcamento_diario:.2f}. "
        f"Estilo: {estilo}. Interesses: {interesses}."
    )

    try:
        model = ChatGroq(
            model=model_name,
            api_key=api_key,
            temperature=0.2,
        )
        graph = construir_grafo(model)
        with st.status("Os agentes estão colaborando...", expanded=True) as status:
            st.write("🔎 Agente Pesquisador analisando o destino...")
            result = graph.invoke({"messages": [HumanMessage(content=request)]})
            st.write("🗺️ Agente Planejador organizando o roteiro...")
            status.update(label="Roteiro pronto!", state="complete", expanded=False)

        final_message = result["messages"][-1]
        st.success("Roteiro gerado com sucesso")
        renderizar_roteiro(final_message.content)
    except Exception as error:
        error_text = str(error)
        if "model_not_found" in error_text or "does not exist" in error_text:
            st.error(
                "O modelo configurado não está disponível para esta chave Groq. "
                "Atualize a página e tente novamente."
            )
        else:
            st.error(f"Não foi possível gerar o roteiro: {error}")
        st.caption(
            "Se o erro continuar, revogue a chave exposta anteriormente, gere uma "
            "nova chave no Groq Console e tente novamente."
        )


if __name__ == "__main__":
    principal()
