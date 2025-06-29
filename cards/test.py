# cards/tests.py
from django.test import TestCase
from django.urls import reverse, resolve
from .views import submit_card, submission_success

class URLsTestCase(TestCase):
    def test_submission_success_url(self):
        url = reverse('cards:submission_success')
        self.assertEqual(url, '/cards/submission-success/')
        self.assertEqual(resolve(url).func, submission_success)

    def test_submit_redirect(self):
        # This would need proper form data and authentication
        response = self.client.post(reverse('cards:submit'), {})
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(response.url.startswith('/cards/submission-success/'))