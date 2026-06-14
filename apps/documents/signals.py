from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Document
from .tasks import process_document_task

@receiver(post_save, sender=Document)
def trigger_document_processing(sender, instance, created, **kwargs):
    # If the document has just been created (not updated) and its status is 'pending'
    if created and instance.status == 'pending':
        # Calling the Celery task asynchronously via .delay()
        process_document_task.delay(instance.id)