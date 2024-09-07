import os
import logging
import shutil

from pathlib import Path
from typing import List
import time

from langchain.indexes import SQLRecordManager, index
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from PyPDF2 import PdfReader
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.DEBUG)

# Configuration
chunk_size = 1024
chunk_overlap = 50
embeddings_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
DOC_TO_ADD_FOLDER = "./docs_folders/doc_to_add"
PROCESSED_DOCS_FOLDER = "./docs_folders/processed_docs"

class ChromaDBManager:
    def __init__(self, persist_directory: str):
        self.persist_directory = persist_directory

    def process_pdfs(self, pdf_storage_path: str) -> List[Document]:
        pdf_directory = Path(pdf_storage_path)
        docs = []  # type: List[Document]
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

        for pdf_path in pdf_directory.glob("*.pdf"):
            logging.info(f"Processing PDF: {pdf_path.name}")
            loader = PyMuPDFLoader(str(pdf_path))
            documents = loader.load()

            # Extracting metadata
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                metadata_dict = {
                    "producer": reader.metadata.producer,
                    "creator": reader.metadata.creator
                }

            for i, doc in enumerate(documents):
                metadata_dict["chunk_number"] = i
                doc.metadata = metadata_dict

            docs += text_splitter.split_documents(documents)

        return docs

    def check_or_create_chroma_db(self, pdf_storage_path: str) -> Chroma:
        """
        Vérifie l'existence de la base de données Chroma. Si elle n'existe pas, la crée à partir des documents PDF.
        Si elle existe, vérifie s'il y a des nouveaux documents à ajouter.
        Retourne l'objet Chroma.
        """
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            logging.info("Loading existing Chroma database...")
            db = self.load_chroma_db()
        else:
            logging.info("Creating new Chroma database...")
            db = self.create_empty_chroma_db()

        self.add_documents_to_chroma_db(pdf_storage_path, db)

        return db

    def load_chroma_db(self) -> Chroma:
        """
        Charge la base de données Chroma depuis le répertoire persistant.
        """
        return Chroma(persist_directory=self.persist_directory, embedding_function=embeddings_model)

    def create_empty_chroma_db(self) -> Chroma:
        """
        Crée une base de données Chroma vide.
        """
        if not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory)

        logging.info("Creating empty Chroma database...")
        db = Chroma(persist_directory=self.persist_directory, embedding_function=embeddings_model)

        namespace = "chromadb/my_documents"
        record_manager = SQLRecordManager(
            namespace, db_url="sqlite:///record_manager_cache.sql"
        )
        logging.info("Creating record_manager...")
        record_manager.create_schema()

        return db

    def add_documents_to_chroma_db(self, pdf_storage_path: str, db: Chroma):
        """
        Ajoute de nouveaux documents PDF à la base de données Chroma existante.
        """
        logging.info("Checking for new documents to add...")
        docs_to_add = self.process_pdfs(DOC_TO_ADD_FOLDER)
        if docs_to_add:
            logging.info(f"Found {len(docs_to_add)} new documents to add to the database.")
            record_manager = SQLRecordManager(
                "chromadb/my_documents", db_url="sqlite:///record_manager_cache.sql"
            )
            index_result = index(
                docs_to_add,
                record_manager,
                db,
                cleanup="incremental",
                source_id_key="chunk_number",
            )
            logging.info(f"Indexing stats: {index_result}")
            self.move_processed_files(DOC_TO_ADD_FOLDER, PROCESSED_DOCS_FOLDER)

    def move_processed_files(self, source_folder: str, destination_folder: str):
        """
        Déplace les fichiers traités vers un dossier de destination.
        """
        for document_path in os.listdir(source_folder):
            filename = os.path.basename(document_path)
            destination_path = os.path.join(destination_folder, filename)
            logging.debug(f"Moving document from {source_folder + '/' + document_path} to {destination_path}")
            try:
                shutil.move(source_folder + "/" + document_path, destination_path)
                logging.debug("Document moved successfully.")
            except Exception as e:
                logging.error(f"Failed to move document: {e}")

    def monitor_folder_for_new_documents(self, folder_path, processed_docs_folder):
        observer = Observer()
        event_handler = NewDocumentHandler(processed_docs_folder)
        observer.schedule(event_handler, folder_path, recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

class NewDocumentHandler(FileSystemEventHandler):
    def __init__(self, processed_docs_folder):
        super().__init__()
        self.processed_docs_folder = processed_docs_folder

    def on_created(self, event):
        if event.is_directory:
            return

        new_document_path = event.src_path
        if new_document_path.lower().endswith('.pdf'):
            ChromaDBManager.move_processed_files(DOC_TO_ADD_FOLDER, self.processed_docs_folder)