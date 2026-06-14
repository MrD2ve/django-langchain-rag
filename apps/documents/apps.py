from django.apps import AppConfig

class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'

    def ready(self):
        # Import signals so Django registers them
        import apps.documents.signals