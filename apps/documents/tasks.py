import os
from celery import shared_task
from django.conf import settings
from .models import Document, DocumentChunk

# AI tool imports from LangChain
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings


@shared_task
def process_document_task(document_id):
    """
    A Celery background task for processing the uploaded PDF.
    Breaks the text into chunks, generates embeddings using LangChain, and saves it in a PGVector.
    """
    try:
        # 1. Finding a document in the database
        document = Document.objects.get(id=document_id)
        document.status = 'processing'
        document.save()

        # 2. Loading and parsing a PDF file using LangChain
        # Passing a local path to a file in the Docker container's file system
        loader = PyPDFLoader(document.file.path)
        pages = loader.load()

        # 3. We cut the text into meaningful chunks.
        # chunk_size=1000 characters, chunk_overlap=200 characters of overlap to maintain context
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_documents(pages)

        # 4. Initializing the embedding model via the OpenRouter proxy
        # (We use the standard text-embedding-3-small model or similar)
        embeddings_model = OpenAIEmbeddings(
            # We take the key from the settings or environment variables (we will add it to .env later)
            openai_api_key=os.getenv("OPENROUTER_API_KEY", "your-fallback-key"),
            openai_api_base="https://openrouter.ai/api/v1",
            model="openai/text-embedding-3-small"
        )

        # 5. The cycle of processing and saving each piece of text
        for chunk in chunks:
            # We transform a piece of text into a vector of numbers (the mathematical meaning of the text)
            vector = embeddings_model.embed_query(chunk.page_content)

            # We store the chunk, its vector, and metadata (e.g., page number) in PostgreSQL
            DocumentChunk.objects.create(
                document=document,
                content=chunk.page_content,
                embedding=vector,
                meta_data=chunk.metadata
            )

        # If everything went without errors, we update the status
        document.status = 'success'
        document.save()

    except Exception as e:
        # If something goes wrong (API crashes, file is corrupted, etc.), we log the error.
        if 'document' in locals():
            document.status = 'error'
            document.error_message = str(e)
            document.save()
        raise e