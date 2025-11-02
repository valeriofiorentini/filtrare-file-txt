# Ricerca Full-Text di file `.txt` con Elasticsearch e Streamlit

ccd ..cd cd .cd cdUtilizza Elasticsearch per un'indicizzazione e una ricerca full-text, e Streamlit per un'interfaccia utente semplice e interattiva.

## Caratteristiche Principali

- **Indicizzazione**: indicizza tutti i file `.txt` in una cartella specificata
- **Ricerca**: cerca per **nome file**, **contenuto** o **entrambi**.
- **Phrase query**: cerca frasi esatte tra virgolette o con checkbox dedicata

## Stack Tecnologico

- **Backend**: Python 3.13+
- **Motore di Ricerca**: Elasticsearch 9.2.0
- **Frontend**: Streamlit
- **Librerie principali**:
  - [`elasticsearch`](https://pypi.org/project/elasticsearch/)
  - [`streamlit`](https://pypi.org/project/streamlit/)
  - [`pydantic`](https://pypi.org/project/pydantic/)

---

## Prerequisiti

- Python 3.12+ installato
- Elasticsearch 9.2.0 in esecuzione (locale o su Docker / Elastic Cloud)

---

## Installazione

### Clonare il repository
0. **salvare repository in locale**

```bash

git clone https://github.com/valeriofiorentini/filtrare-file-txt.git
cd filtrare-file-txt
```
### Setup Ambiente

1. **Creazione ambiente virtuale**

```bash

uv venv
uv sync
```

### 2 Avvio container Elasticsearch

```bash

docker-compose up -d
```

