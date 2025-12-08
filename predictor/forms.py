# predictor/forms.py
from django import forms

TYPE_LOCAL_CHOICES = [
    ('maison', 'Maison'),
    ('appartement', 'Appartement'),
]


class PredictForm(forms.Form):
    surface_bati = forms.IntegerField(label="Surface bâtie (m²)", min_value=20)
    nombre_pieces = forms.IntegerField(label="Nombre de pièces", min_value=1)
    type_local = forms.ChoiceField(label="Type de local", choices=TYPE_LOCAL_CHOICES)
    surface_terrain = forms.IntegerField(label="Surface terrain (m²)", min_value=20)
    nombre_lots = forms.IntegerField(label="Nombre de lots", min_value=1, initial=1)

    def clean_surface_terrain(self):
        val = self.cleaned_data.get('surface_terrain')
        # Si vide, on met zéro
        return val or 0
