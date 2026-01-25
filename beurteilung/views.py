from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden, HttpResponse
from django.utils import timezone

from django.contrib.admin.views.decorators import staff_member_required
from .services.pdf import generate_evaluation_pdf_bytes
from .models import EvaluationRequest, Evaluation
from .forms import EvaluationForm
from django.core.files.base import ContentFile
from .services.email import send_evaluation_pdf_email

def evaluations_view(request, token):
    evaluation_request = get_object_or_404(
        EvaluationRequest,
        token=token
    )

    if not evaluation_request.is_valid():
        return HttpResponseForbidden(
            "Dieser Link ist ungültig oder abgelaufen"
        )
    
    if request.method == "POST":
        form = EvaluationForm(request.POST)
        if form.is_valid():
            evaluation = Evaluation.objects.create(
                evaluation_request=evaluation_request,
                rating=form.cleaned_data["rating"],
                comment=form.cleaned_data["comment"],
                ip_address=request.META.get("REMOTE_ADDR", ""),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

            # EvaluationRequest sperren
            evaluation_request.is_used = True
            evaluation_request.save(update_fields=["is_used"])

            # PDF erzeugen
            pdf_bytes = generate_evaluation_pdf_bytes(evaluation)
            filename = f"evaluation_{evaluation.id}.pdf"
            evaluation.pdf_file.save(filename, ContentFile(pdf_bytes))
            evaluation.save(update_fields=["pdf_file"])

            # E-Mail an Supervisor senden
            send_evaluation_pdf_email(evaluation)

            return render(request, "beurteilung/evaluation_done.html")
    else:
        form = EvaluationForm()

    return render(
        request,
        "beurteilung/evaluation_form.html",
        {
            "form": form,
            "person": evaluation_request.person,
            "supervisor":evaluation_request.supervisor,
        }
    )

@staff_member_required
def evaluation_pdf_view(request, evaluation_id):
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    pdf_bytes = generate_evaluation_pdf_bytes(evaluation)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    filename = f"Beurteilung-{evaluation.id}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response