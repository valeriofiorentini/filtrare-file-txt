import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(PROJECT_ROOT)

import streamlit as st
from app.business.operation_elasticsearch import run_indexing, search_documents, check_index_exists, \
    get_elasticsearch_client
from app.models.models import config

if 'page' not in st.session_state:
    st.session_state.page = 1
if 'page_size' not in st.session_state:
    st.session_state.page_size = 10


def reset_page_callback():
    st.session_state.page = 1


st.set_page_config(
    page_title="Ricerca File",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Ricerca File con Elasticsearch")

st.sidebar.title("Amministrazione")

if st.sidebar.button("Avvia/Aggiorna Indicizzazione", type="primary"):
    with st.spinner("Indicizzazione in corso..."):
        es_client = get_elasticsearch_client()
        if not es_client:
            st.error("Impossibile connettersi a Elasticsearch. Controlla la configurazione.")
            st.stop()

        progress_bar = st.progress(0, text="Indicizzazione documenti...")
        result = run_indexing(es_client, progress_bar)

        if result["success"]:
            if result["index_created"]:
                st.success(f"Indice '{config.INDEX_NAME}' creato.")
            else:
                st.info(f"Indice '{config.INDEX_NAME}' già esistente. Documenti aggiornati/aggiunti.")

            st.success(f"Indicizzazione completata in {result['time']:.2f} secondi.")
            st.info(f"Documenti indicizzati con successo: {result['indexed_docs']}")
            if result["errors"] > 0:
                st.warning(f"Si sono verificati {result['errors']} errori.")
        else:
            st.error(f"Errore durante l'indicizzazione: {result['error']}")

st.sidebar.divider()

st.header("🔍 Cerca Documenti")
st.info("Puoi cercare per nome file, per contenuto, o per entrambi contemporaneamente.")

query_nome = st.text_input(
    "Cerca per Nome File:",
    placeholder="es. ilfatto_omicidio",
    on_change=reset_page_callback
)
query_contenuto = st.text_input(
    "Cerca per Contenuto:",
    placeholder="developer",
    on_change=reset_page_callback
)

col1, col2 = st.columns(2)
with col1:
    is_phrase_query = st.checkbox(
        "Cerca frase esatta (solo per Contenuto)",
        on_change=reset_page_callback
    )
with col2:
    st.slider(
        "Numero di risultati per pagina:", 5, 50,
        key='page_size',
        on_change=reset_page_callback
    )


def get_highlight(hit):
    """
    estrae e formatta il testo da ricerca, controlla se la chiave 'highlight' esiste nel dizionario hit.
    e cerca in diversi campi di highlight ('contenuto_file.italian', 'contenuto_file.english', 'contenuto_file', 'nome_file')

    :param hit: risultato restituito da elasticsearch.
    :return:
    """

    if 'highlight' not in hit:
        return ""
    if 'contenuto_file.italian' in hit['highlight']:
        return "...".join(hit['highlight']['contenuto_file.italian'])
    if 'contenuto_file.english' in hit['highlight']:
        return "...".join(hit['highlight']['contenuto_file.english'])
    if 'contenuto_file' in hit['highlight']:
        return "...".join(hit['highlight']['contenuto_file'])
    if 'nome_file' in hit['highlight']:
        return "...".join(hit['highlight']['nome_file'])
    return ""


if query_nome or query_contenuto:
    es_client = get_elasticsearch_client()
    if not es_client:
        st.error("Impossibile connettersi a Elasticsearch. Controlla la configurazione.")
        st.stop()

    try:
        exists, doc_count = check_index_exists(es_client)
        if not exists:
            st.info(f"L'indice '{config.INDEX_NAME}' non esiste. Avvio dell'indicizzazione automatica...")
            with st.spinner("Creazione indice in corso... (potrebbe richiedere tempo)"):
                result = run_indexing(es_client)
                if not result["success"]:
                    st.error(f"Indicizzazione automatica fallita: {result['error']}")
                    st.stop()
            st.success("Indicizzazione completata. Esecuzione della ricerca...")
        elif doc_count == 0:
            st.warning(f"L'indice '{config.INDEX_NAME}' esiste ma è vuoto. Avvia l'indicizzazione dalla sidebar.")

    except Exception as e:
        st.error(f"Errore durante il controllo/creazione dell'indice: {e}")
        st.stop()

    result = search_documents(
        es_client,
        query_nome_file=query_nome,
        query_contenuto=query_contenuto,
        is_phrase_query=is_phrase_query,
        page=st.session_state.page,
        page_size=st.session_state.page_size
    )

    if result["success"]:
        st.success(f"Trovati **{result['total_hits']}** risultati in {result['time']:.4f} secondi.")

        if not result["hits"]:
            st.warning("Nessun documento trovato.")
        else:
            for i, hit in enumerate(result["hits"]):
                score = hit['_score']
                source = hit['_source']
                highlight_snippet = get_highlight(hit)

                with st.container(border=True):
                    st.markdown(
                        f"**{(st.session_state.page - 1) * st.session_state.page_size + i + 1}. {source['nome_file']}** (Score: `{score:.2f}`)")
                    st.caption(f"Percorso: `{source['percorso_completo']}`")

                    if highlight_snippet:
                        st.markdown(f"**Corrispondenza:** {highlight_snippet}", unsafe_allow_html=True)

                    with st.expander("Mostra anteprima contenuto"):
                        snippet = source.get('contenuto_file', '')[:500]
                        st.code(snippet + "..." if len(snippet) >= 500 else snippet, language=None)

            total_pages = (result['total_hits'] + st.session_state.page_size - 1) // st.session_state.page_size

            if total_pages > 1:
                st.markdown("---")
                cols = st.columns([1, 2, 1])

                with cols[1]:
                    new_page = st.number_input(
                        "Vai a pagina:",
                        min_value=1,
                        max_value=total_pages,
                        value=st.session_state.page,
                        step=1,
                        key='page_input'
                    )
                    if new_page != st.session_state.page:
                        st.session_state.page = new_page
                        st.rerun()

                st.markdown(
                    f"<div style='text-align: center; padding: 10px;'>Pagina {st.session_state.page} di {total_pages}</div>",
                    unsafe_allow_html=True)
    else:
        st.error(f"Errore durante la ricerca: {result['error']}")