from django.urls import path
from .views import RAGChatView

urlpatterns = [
    path('ask/', RAGChatView.as_view(), name='rag_ask'),
]