import os
import glob
from typing import Generator, Dict, Any
from app.models.models import config, FileDocument
from app.utils.logger_config import logger_index_txt



def file_data_generator(directory_path: str) -> Generator[Dict[str, Any], None, None]:
    """
    genera documenti da indicizzare partendo dai file .txt in una directory
    per ogni file, legge il contenuto, estrae il nome e il percorso completo.
    crea un oggetto filedocument e lo restituisce come dizionario

    :param directory_path: percorso della directory da scansionare.
    :return:
    """

    for file_path in glob.glob(os.path.join(directory_path, "*.txt")):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            file_name = os.path.basename(file_path)
            doc = FileDocument(
                nome_file=file_name,
                contenuto_file=content,
                percorso_completo=file_path
            )
            yield {"_index": config.INDEX_NAME, "_source": doc.model_dump()}
        except Exception as e:
            logger_index_txt.error(f"Errore nel file {file_path}: {e}")