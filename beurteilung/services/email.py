from django.core.mail import EmailMessage

def send_evaluation_pdf_email(evaluation):
    """
    Send evaluation PDF to the supervisor
    """
    if not evaluation.pdf_file:
        raise ValueError("PDF not generated yet")

    subject = f"Beurteilung für {evaluation.evaluation_request.person}"
    body = (
        f"Sehr geehrte/r {evaluation.evaluation_request.supervisor.nachname},\n\n"
        "anbei die digitale Beurteilung.\n"
        "Die Bewertung ist signiert und revisionssicher.\n\n"
        "Viele Grüße"
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=None,  # DEFAULT_FROM_EMAIL oder leer für Django Default
        to=[evaluation.evaluation_request.supervisor.email],
    )

    # PDF anhängen
    email.attach(
        f"evaluation_{evaluation.id}.pdf",
        evaluation.pdf_file.read(),
        "application/pdf"
    )

    email.send(fail_silently=False)