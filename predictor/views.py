# predictor/views.py
import requests
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .forms import PredictForm
from django.contrib import messages
import base64


FASTAPI_URL = settings.FASTAPI_BASE_URL.rstrip('/') + settings.FASTAPI_PREDICT_ROUTE


@require_http_methods(["GET", "POST"])
def predict_view(request):
    """
    GET : affiche le formulaire
    POST: valide le formulaire, envoie la requête JSON à FastAPI, récupère la réponse et l'affiche
    """
    if request.method == 'POST':
        form = PredictForm(request.POST)
        if form.is_valid():
            payload = {
                "surface_bati": form.cleaned_data['surface_bati'],
                "nombre_pieces": form.cleaned_data['nombre_pieces'],
                "type_local": form.cleaned_data['type_local'],
                "surface_terrain": form.cleaned_data['surface_terrain'],
                "nombre_lots": form.cleaned_data['nombre_lots'],
            }

            try:
                # Encodage Basic Auth
                userpass = f"{settings.FASTAPI_USERNAME}:{settings.FASTAPI_PASSWORD}"
                token = base64.b64encode(userpass.encode()).decode()

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {token}"
                }

                resp = requests.post(
                    FASTAPI_URL,
                    json=payload,
                    headers=headers,
                    timeout=10
                    )

                if resp.status_code == 401:
                    messages.error(request, "Identifiants invalides pour l'API FastAPI.")
                    return render(request, "predictor/form.html", {"form": form})

                resp.raise_for_status()
                data = resp.json()

                # Vérification basique de la réponse attendue
                expected_keys = {'prix_m2_estime', 'ville_modele', 'model'}
                if not expected_keys.issubset(set(data.keys())):
                    messages.error(request, "Réponse inattendue de l'API.")
                    return render(request, 'predictor/form.html', {'form': form})

                # Afficher le résultat
                return render(request, 'predictor/result.html', {
                    'input': payload,
                    'result': data
                })

            except requests.exceptions.RequestException as e:
                # Problème réseau / timeout / 5xx etc
                messages.error(request, f"Erreur lors de la communication avec le service de prédiction: {e}")
        else:
            messages.error(request, "Formulaire invalide — vérifie les champs.")
    else:
        form = PredictForm()

    return render(request, 'predictor/form.html', {'form': form})
