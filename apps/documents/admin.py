from django.contrib import admin
from .models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    # Which columns to show in the file list
    list_display = ('title', 'status', 'created_at')
    # We prohibit manual editing of the status (it is changed by Celery)
    readonly_fields = ('status', 'error_message')


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'content_snippet')

    def content_snippet(self, obj):
        return obj.content[:50] + "..." if obj.content else ""

    content_snippet.short_description = 'A piece of text'