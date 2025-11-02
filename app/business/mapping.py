def get_mapping():
    """
    definisce la struttura (mapping) e gli analyzer per l'indice elasticsearch.

    :return: dizionario di mapping completo
    """

    return {
        "settings": {
            "analysis": {
                "tokenizer": {
                    "ngram_tokenizer": {
                        "type": "ngram",
                        "min_gram": 2,
                        "max_gram": 20,
                        "token_chars": ["letter", "digit"]
                    }
                },
                "filter": {
                    "stemmer": {
                        "type": "stemmer",
                        "name": "italian"
                    }
                },
                "analyzer": {
                    "filename_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "stop", "asciifolding"]
                    },
                    "content_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "stop", "asciifolding", "stemmer"]
                    },
                    "search_analyzer": {
                        "type": "custom",
                        "tokenizer": "keyword",
                        "filter": ["lowercase"]
                    },
                    "ngram_analyzer": {
                        "type": "custom",
                        "tokenizer": "ngram_tokenizer",
                        "filter": ["lowercase", "asciifolding"]
                    }
                },
            }
        },
        "mappings": {
            "properties": {
                "nome_file": {
                    "type": "text",
                    "analyzer": "filename_analyzer",
                    "search_analyzer": "search_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "ngram": {"type": "text", "analyzer": "ngram_analyzer"}
                    }
                },
                "contenuto_file": {
                    "type": "text",
                    "analyzer": "content_analyzer",
                    "search_analyzer": "search_analyzer",
                    "fields": {
                        "italian": {"type": "text", "analyzer": "italian"},
                        "english": {"type": "text", "analyzer": "english"}
                    }
                },
                "percorso_completo": {"type": "keyword"}
            }
        }
    }
