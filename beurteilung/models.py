import uuid
import hmac
import hashlib

from django.conf import settings
from django.db import models
from django.utils import timezone
from personal.models import Mitarbeiter
from ansprechpartner.models import Ansprechpartner
import os

def evaluation_pdf_upload_path(instance, filename):
    return os.path.join(
        "evaluation_pdfs",
        f"evaluation_{instance.id}.pdf"
    )
class Supervisor(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()

    def __str__(self):
        return f"{self.name} - {self.email}"

class EvaluationRequest(models.Model):
    person = models.ForeignKey(Mitarbeiter, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(Ansprechpartner, on_delete=models.CASCADE)

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return(
            not self.is_used
            and timezone.now() < self.expires_at
        )
    
    def __str__(self):
        return f"Beurteilung für {self.person.nachname} mit {self.supervisor.vorname} {self.supervisor.nachname}"
    
class Evaluation(models.Model):
    evaluation_request = models.OneToOneField(EvaluationRequest, related_name="evaluation", on_delete=models.CASCADE)

    rating = models.IntegerField()
    comment = models.TextField()

    submitted_at = models.DateTimeField(auto_now_add=True)

    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()

    signature = models.CharField(max_length=64, editable=False)

    pdf_file = models.FileField(
        upload_to=evaluation_pdf_upload_path,
        null=True,
        blank=True
    )

    def canonical_data(self) -> str:
        return "|".join([
            str(self.evaluation_request.id),
            str(self.rating),
            self.comment.strip(),
            self.submitted_at.isoformat(),
            self.ip_address,
            self.user_agent
        ])
    
    def generate_signature(self) -> str:
        return hmac.new(
            key=settings.SECRET_KEY.encode(),
            msg=self.canonical_data().encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
    
    def verify_signature(self) -> bool:
        excepted = self.generate_signature()
        return hmac.compare_digest(excepted, self.signature)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.signature:
            self.signature = self.generate_signature()
            super().save(update_fields=["signature"])
        

    def __str__(self):
        return f"Evaluation #{self.id}"