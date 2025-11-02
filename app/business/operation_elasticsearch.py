import time
import streamlit as st
from typing import List
from elasticsearch import Elasticsearch, helpers

from app.business.operation_file import file_data_generator
from app.models.models import config
from app.utils.logger_config import logger_index_txt
from app.business.mapping import get_mapping


def get_elasticsearch_client():
    """
     stabilisce e restituisce una connessione al client elasticsearch.

    :return: un'istanza di elasticsearch se la connessione ha successo
    """

    try:
        client = Elasticsearch(
            config.ELASTICSEARCH_HOST,
            verify_certs=False,
            request_timeout=30,
        )
        try:
            if not client.ping():
                info = client.info()
                if not info:
                    raise ConnectionError("Ping fallito")
        except Exception:
            info = client.info()
            if not info:
                raise ConnectionError("Connessione fallita")
        return client
    except Exception as e:
        st.error(f"❌ Connessione fallita: {e}")
        return None



def create_index(es: Elasticsearch) -> bool:
    """
    creazione dell'indice su elasticsearch se non esiste già

    :param es: l'istanza del client elasticsearch.
    :return: true se l'indice è stato creato, false se esisteva già.
    """

    try:
        if not es.indices.exists(index=config.INDEX_NAME):
            es.indices.create(
                index=config.INDEX_NAME,
                body={
                    "settings": {
                        "index.max_ngram_diff": 18,
                        "analysis": get_mapping().get("settings", {}).get("analysis", {})
                    },
                    "mappings": get_mapping()["mappings"]
                }
            )
            logger_index_txt.info(f"Indice '{config.INDEX_NAME}' creato con max_ngram_diff=18.")
            return True
        else:
            logger_index_txt.info(f"Indice '{config.INDEX_NAME}' già esistente.")
            return False
    except Exception as e:
        logger_index_txt.error(f"Errore creazione indice: {e}")
        raise

def run_indexing(es: Elasticsearch, progress_bar=None):
    """
    avvia il processo di indicizzazione, creazione dell'indice tramite create_index().
    poi utilizza helpers.bulk per indicizzare i documenti generati da file_data_generator().
    infine aggiorna l'indice e restituisce un riepilogo dell'operazione.

    :param es: client elasticsearch
    :param progress_bar: oggetto progressbar di streamlit
    :return: dict
    """
    start_time = time.time()
    try:
        index_created = create_index(es)
        gen = file_data_generator(config.DIRECTORY_PATH)

        success, errors = helpers.bulk(
            es,
            gen,
            chunk_size=200,
            request_timeout=60
        )
        if errors:
            logger_index_txt.error(f"Errori bulk indexing: {errors[:5]}")
        es.indices.refresh(index=config.INDEX_NAME)
        total_time = time.time() - start_time
        st.success(f"Indicizzazione completata in {total_time:.2f}s. Documenti: {success}")
        return {"success": True, "index_created": index_created, "indexed_docs": success, "errors": len(errors), "time": total_time}
    except Exception as e:
        logger_index_txt.error(f"Errore indicizzazione: {e}")
        return {"success": False, "error": str(e)}

def check_index_exists(es: Elasticsearch) -> (bool, int):
    """
    controlla se un indice esiste e quanti documenti contiene.

    :param es:  client elasticsearch
    :return: dove il primo elemento indica se l'indice esiste e il secondo è il numero di documenti
    """
    try:
        if not es.indices.exists(index=config.INDEX_NAME):
            return False, 0
        count_response = es.count(index=config.INDEX_NAME)
        doc_count = count_response.get('count', 0)
        return True, doc_count
    except Exception as e:
        logger_index_txt.error(f"Errore nel controllare l'indice {config.INDEX_NAME}: {e}")
        return False, 0


def search_documents(es: Elasticsearch, query_nome_file: str, query_contenuto: str, is_phrase_query: bool = False,
                     selected_sources: List[str] = None, page: int = 1, page_size: int = 10):
    """
    costruisce una query bool elasticsearch per combinare le ricerche su nome file e contenuto.
    utilizza dei controlli 'should' per dare punteggi più alti a documenti che corrispondono a entrambi i criteri.
    per la ricerca nel contenuto, supporta ricerche standard e phrase query.

    :param es: client elasticsearch
    :param query_nome_file: termine di ricerca nel nome
    :param query_contenuto: termine di ricerca nel contenuto
    :param is_phrase_query: se true, cerca frase esatta nel contenuto
    :param selected_sources:  filtra risultati per nome file
    :param page:  numero di pagina per paginazion
    :param page_size:  risultati per pagina
    :return:
    """

    bool_clauses = []
    highlight_fields = {}

    if query_nome_file:
        bool_clauses.append({
            "multi_match": {
                "query": query_nome_file,
                "fields": ["nome_file^5", "nome_file.keyword^10", "nome_file.ngram^3"],
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        })
        highlight_fields["nome_file"] = {"pre_tags": ["<mark>"], "post_tags": ["</mark>"]}

    if query_contenuto:
        query_type = "phrase" if is_phrase_query else "best_fields"

        query_params = {
            "query": query_contenuto,
            "fields": ["contenuto_file^2", "contenuto_file.italian^3", "contenuto_file.english^3"],
            "type": query_type,
            "slop": 2 if is_phrase_query else 0
        }

        if not is_phrase_query:
            query_params["fuzziness"] = "AUTO"
            query_params["prefix_length"] = 1

        bool_clauses.append({"multi_match": query_params})

        highlight_fields["contenuto_file"] = {"pre_tags": ["<mark>"], "post_tags": ["</mark>"], "fragment_size": 150,
                                              "number_of_fragments": 3}
        highlight_fields["contenuto_file.italian"] = {"pre_tags": ["<mark>"], "post_tags": ["</mark>"],
                                                      "fragment_size": 150, "number_of_fragments": 3}
        highlight_fields["contenuto_file.english"] = {"pre_tags": ["<mark>"], "post_tags": ["</mark>"],
                                                      "fragment_size": 150, "number_of_fragments": 3}

    if not bool_clauses:
        return {"success": True, "hits": [], "total_hits": 0, "aggregations": {}, "time": 0}

    main_query = {"bool": {"should": bool_clauses, "minimum_should_match": 1}}

    if selected_sources:
        main_query = {"bool": {"must": [main_query], "filter": {"terms": {"nome_file.keyword": selected_sources}}}}

    es_query = {
        "query": main_query,
        "highlight": {
            "fields": highlight_fields,
            "order": "score",
            "number_of_fragments": 1,
            "max_analyzed_offset": 1000000
        },
        "aggs": {"sources": {"terms": {"field": "nome_file.keyword", "size": 20}}},
        "from": (page - 1) * page_size,
        "size": page_size
    }

    try:
        start_search = time.time()
        res = es.search(index=config.INDEX_NAME, body=es_query)
        end_search = time.time()
        hits = res["hits"]["hits"]
        total_hits = res["hits"]["total"]["value"]
        aggregations = res.get("aggregations", {})
        logger_index_txt.info(
            f"Trovati {total_hits} risultati per nome='{query_nome_file}', contenuto='{query_contenuto}' in {end_search - start_search:.4f}s.")
        return {"success": True, "hits": hits, "total_hits": total_hits, "aggregations": aggregations,
                "time": end_search - start_search}
    except Exception as e:
        logger_index_txt.error(f"Errore ricerca: {e}")
        if "index_not_found_exception" in str(e):
            logger_index_txt.warning(f"Tentativo di ricerca sull'indice non esistente: {config.INDEX_NAME}")
            return {"success": True, "hits": [], "total_hits": 0, "aggregations": {}, "time": 0}
        return {"success": False, "error": str(e)}


def get_all_sources(es: Elasticsearch) -> List[str]:
    """
    recupera l'elenco di tutti i nomi file indicizzati

    :param es: client elasticsearch.
    :return:  una lista di stringhe con i nomi dei file.
    """

    es_query = {"size": 0, "aggs": {"all_sources": {"terms": {"field": "nome_file.keyword", "size": 500}}}}
    try:
        res = es.search(index=config.INDEX_NAME, body=es_query)
        buckets = res['aggregations']['all_sources']['buckets']
        return sorted([bucket['key'] for bucket in buckets])
    except Exception as e:
        logger_index_txt.error(f"Errore recupero fonti: {e}")
        return []