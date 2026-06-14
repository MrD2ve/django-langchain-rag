from pgvector.django import L2Distance
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.documents.models import DocumentChunk

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


class RAGChatView(APIView):
    """
    API endpoint for document chat using LangChain and PGVector.
    """

    def post(self, request):
        question = request.data.get('question')
        if not question:
            return Response({"error": "The question cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Initialize the embedding model (the same as when creating chunks)
            embeddings_model = OpenAIEmbeddings(
                openai_api_key=os.getenv("OPENROUTER_API_KEY", "your-key"),
                openai_api_base="https://openrouter.ai/api/v1",
                model="openai/text-embedding-3-small"
            )

            # 2. Translating the user's question into a vector of numbers
            question_vector = embeddings_model.embed_query(question)

            # 3. Using L2Distance to Correctly Calculate Euclidean Distance in Django ORM
            raw_chunks = DocumentChunk.objects.order_by(
                L2Distance('embedding', question_vector)
            )[:3]

            # We collect the found text into a single context
            context = "\n\n".join([chunk.content for chunk in raw_chunks])

            # 4. Creating a prompt template for LangChain
            prompt_template = ChatPromptTemplate.from_template(
                "You are a professional backend developer and academic assistant. "
                "Use ONLY the context provided below to fully answer the question. "
                "If there is no answer in the context, just say so, don’t make up anything on your own.\n\n"
                "Context:\n{context}\n\n"
                "Question: {question}\n\n"
                "Answer:"
            )

            # 5. Initializing the language model via OpenRouter
            llm = ChatOpenAI(
                openai_api_key=os.getenv("OPENROUTER_API_KEY", "your-key"),
                openai_api_base="https://openrouter.ai/api/v1",
                model="nvidia/nemotron-3-super-120b-a12b:free"
            )

            # 6. Assembling a LangChain Expression Language (LCEL) chain
            # It will automatically insert the context and question into the prompt, send it to LLM and parse the response into a string.
            chain = (
                    prompt_template
                    | llm
                    | StrOutputParser()
            )

            # Start the chain
            ai_response = chain.invoke({"context": context, "question": question})

            return Response({
                "question": question,
                "answer": ai_response,
                "sources": [
                    {"chunk_id": c.id, "doc_title": c.document.title, "page": c.meta_data.get('page', 0) + 1}
                    for c in raw_chunks
                ]
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)