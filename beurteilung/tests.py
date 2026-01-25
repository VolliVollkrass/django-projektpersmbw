from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from .models import Person, Supervisor, EvaluationRequest, Evaluation


class EvaluationFlowTest(TestCase):

    def setUp(self):
        self.person = Person.objects.create(
            first_name="Max",
            last_name="Mustermann"
        )

        self.supervisor = Supervisor.objects.create(
            name="Erika Beispiel",
            email="erika@example.com"
        )

        self.request = EvaluationRequest.objects.create(
            person=self.person,
            supervisor=self.supervisor,
            expires_at=timezone.now() + timedelta(days=1)
        )

    def test_full_evaluation_flow(self):
        url = f"/evaluation/{self.request.token}/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, {
            "rating": 5,
            "comment": "Top Leistung"
        })

        self.assertEqual(response.status_code, 200)

        self.request.refresh_from_db()
        self.assertTrue(self.request.is_used)

        evaluation = Evaluation.objects.get(
            evaluation_request=self.request
        )

        self.assertTrue(evaluation.verify_signature())