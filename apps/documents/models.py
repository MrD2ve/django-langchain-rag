from django.db import models
from pgvector.django import VectorField

class Document(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Awaiting processing'),
        ('processing', 'In the process of indexing'),
        ('success', 'Successfully processed'),
        ('error', 'Processing error'),
    ]

    title = models.CharField(max_length=255, verbose_name="File name")
    file = models.FileField(upload_to='documents/', verbose_name="Document file")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    error_message = models.TextField(blank=True, null=True, verbose_name="Error message")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField(verbose_name="Piece text")

    # Field for storing a vector.
    # Dimension=1536 is the standard vector size for most popular embedding models (e.g. from OpenAI)
    embedding = VectorField(dimensions=1536, null=True, blank=True)

    # It is useful to store metadata (for example, the page number where the piece is taken from)
    meta_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Chunk {self.id} for {self.document.title}"