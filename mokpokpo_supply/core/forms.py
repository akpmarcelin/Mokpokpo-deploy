# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur


class UtilisateurCreationForm(UserCreationForm):
    nom = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom de famille'
        })
    )

    prenom = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre prénom'
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre@email.com'
        })
    )

    telephone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+228XXXXXXXX'
        })
    )

    localisation = forms.CharField(
        required=False,
        help_text="Cliquez sur la carte pour définir votre position",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Latitude,Longitude',
            'readonly': 'readonly'
        })
    )

    class Meta:
        model = Utilisateur
        fields = (
            'username',
            'nom',
            'prenom',
            'email',
            'telephone',
            'localisation',
            'password1',
            'password2'
        )

    def clean_localisation(self):
        """
        Validation du format GPS: latitude,longitude
        """
        localisation = self.cleaned_data.get('localisation')

        if localisation:
            try:
                lat, lng = localisation.split(',')
                float(lat)
                float(lng)
            except ValueError:
                raise forms.ValidationError(
                    "Localisation invalide. Veuillez choisir un point sur la carte."
                )

        return localisation

    def save(self, commit=True):
        """
        Conversion localisation -> latitude / longitude
        """
        user = super().save(commit=False)

        localisation = self.cleaned_data.get('localisation')
        if localisation:
            lat, lng = localisation.split(',')
            user.latitude = float(lat)
            user.longitude = float(lng)

        if commit:
            user.save()

        return user


# ====================
# FORMULAIRE DE PRÉDICTION ML
# ====================
class MLPredictionForm(forms.Form):
    """Formulaire pour saisir les paramètres de prédiction ML"""
    
    superficie_totale = forms.FloatField(
        label="Surface totale cultivée (hectares)",
        min_value=0.1,
        max_value=1000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '10.5',
            'step': '0.1'
        })
    )
    
    precipitations_mm = forms.FloatField(
        label="Précipitations moyennes (mm)",
        min_value=0,
        max_value=500,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '150',
            'step': '1'
        })
    )
    
    temperature_moyenne = forms.FloatField(
        label="Température moyenne (°C)",
        min_value=10,
        max_value=45,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '25.5',
            'step': '0.1'
        })
    )
    
    age_plants_moyen = forms.FloatField(
        label="Âge moyen des plants (années)",
        min_value=0.5,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '3',
            'step': '0.5'
        })
    )
    
    mois = forms.IntegerField(
        label="Mois de l'année",
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '6'
        })
    )
    
    cout_intrants = forms.FloatField(
        label="Coût des intrants (FCFA/hectare)",
        min_value=1000,
        max_value=1000000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '50000',
            'step': '1000'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des classes Bootstrap pour tous les champs
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        """Validation personnalisée"""
        cleaned_data = super().clean()
        
        # Vérifier que les valeurs sont cohérentes
        superficie = cleaned_data.get('superficie_totale')
        cout_intrants = cleaned_data.get('cout_intrants')
        
        if superficie and cout_intrants:
            # Le coût par hectare ne devrait pas être trop élevé
            cout_par_hectare = cout_intrants / superficie
            if cout_par_hectare > 200000:  # Plus de 200k FCFA/ha semble excessif
                raise forms.ValidationError(
                    "Le coût des intrants par hectare semble trop élevé. "
                    f"Actuel: {cout_par_hectare:,.0f} FCFA/ha"
                )
        
        return cleaned_data

