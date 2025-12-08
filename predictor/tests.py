"""
Tests unitaires pour l'application predictor.
Ces tests vérifient le formulaire et la vue de prédiction.
"""
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.contrib.messages import get_messages
from .forms import PredictForm
from django.conf import settings
import base64
from requests.exceptions import RequestException


class PredictorFormTests(TestCase):
    """Tests pour le formulaire de prédiction."""

    def test_form_valid_data(self):
        """Test que le formulaire est valide avec des données correctes."""
        form_data = {
            'surface_bati': 100,
            'nombre_pieces': 3,
            'type_local': 'appartement',  # valeur interne du ChoiceField
            'surface_terrain': 50,
            'nombre_lots': 1
        }
        form = PredictForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_data(self):
        """Test que le formulaire est invalide avec des données incorrectes."""
        form_data = {
            'surface_bati': '',
            'nombre_pieces': -1,
            'type_local': '',
            'surface_terrain': -10,
            'nombre_lots': 0
        }
        form = PredictForm(data=form_data)
        self.assertFalse(form.is_valid())


class PredictorViewsTests(TestCase):
    """Tests pour la vue de prédiction."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('predictor:predict')  # adapter selon urls.py

    def test_get_renders_form(self):
        """GET doit afficher le formulaire."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

    def test_post_invalid_form(self):
        """POST avec formulaire invalide doit afficher une erreur."""
        response = self.client.post(self.url, data={'surface_bati': ''})
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Formulaire invalide" in str(m) for m in messages))

    @patch('predictor.views.requests.post')
    def test_post_valid_form_success(self, mock_post):
        """POST avec formulaire valide et réponse API correcte."""
        form_data = {
            'surface_bati': 100,
            'nombre_pieces': 3,
            'type_local': 'appartement',
            'surface_terrain': 50,
            'nombre_lots': 1
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'prix_m2_estime': 3500,
            'ville_modele': 'Paris',
            'model': 'XGBoost'
        }
        mock_post.return_value = mock_response

        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('result', response.context)
        self.assertEqual(response.context['result']['prix_m2_estime'], 3500)
        self.assertEqual(response.context['result']['ville_modele'], 'Paris')

        # Vérifier l'auth Basic
        userpass = f"{settings.FASTAPI_USERNAME}:{settings.FASTAPI_PASSWORD}"
        token = base64.b64encode(userpass.encode()).decode()
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('Authorization', kwargs['headers'])
        self.assertEqual(kwargs['headers']['Authorization'], f"Basic {token}")

    @patch('predictor.views.requests.post')
    def test_post_valid_form_api_exception(self, mock_post):
        """POST avec exception lors de l'appel API."""
        form_data = {
            'surface_bati': 100,
            'nombre_pieces': 3,
            'type_local': 'appartement',
            'surface_terrain': 50,
            'nombre_lots': 1
        }

        mock_post.side_effect = RequestException("API down")
        response = self.client.post(self.url, data=form_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Erreur lors de la communication" in str(m) for m in messages))

    @patch('predictor.views.requests.post')
    def test_post_valid_form_invalid_response(self, mock_post):
        """POST avec réponse API manquante des clés attendues."""
        form_data = {
            'surface_bati': 100,
            'nombre_pieces': 3,
            'type_local': 'appartement',
            'surface_terrain': 50,
            'nombre_lots': 1
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'unexpected': 'data'}
        mock_post.return_value = mock_response

        response = self.client.post(self.url, data=form_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Réponse inattendue de l'API" in str(m) for m in messages))

    @patch('predictor.views.requests.post')
    def test_post_valid_form_unauthorized(self, mock_post):
        """POST avec API renvoyant 401 Unauthorized."""
        form_data = {
            'surface_bati': 100,
            'nombre_pieces': 3,
            'type_local': 'appartement',
            'surface_terrain': 50,
            'nombre_lots': 1
        }

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        response = self.client.post(self.url, data=form_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Identifiants invalides pour l'API" in str(m) for m in messages))
