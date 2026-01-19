import pandas as pd
import numpy as np
from datetime import timedelta
from core.models import Produit, Lot, MouvementStock, Livraison

class StockPredictor:
    """
    Modèle simple de prédiction de stock basé sur la consommation historique.
    Peut être remplacé par un vrai modèle ML plus tard.
    """

    def __init__(self):
        # Paramètres simples
        self.prediction_horizon_days = 7  # prévisions sur 7 jours

    def predict_from_db(self):
        """
        Récupère les données de la base et renvoie une liste de prédictions.
        Chaque prédiction est un dict : {'produit': produit_obj, 'date': date, 'quantite_estimee': float}
        """
        predictions = []

        produits = Produit.objects.all()

        for produit in produits:
            # Consommation moyenne par jour : somme des lots sortis pour ce produit
            mouvements = MouvementStock.objects.filter(lot__produit=produit, type_mouvement='SORTIE')
            if not mouvements.exists():
                continue

            df = pd.DataFrame.from_records(mouvements.values('date', 'quantite'))
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').resample('D').sum().fillna(0)

            # Consommation moyenne par jour
            mean_daily = df['quantite'].mean()

            # Générer prédiction pour les 7 prochains jours
            start_date = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)
            for i in range(self.prediction_horizon_days):
                pred_date = start_date + pd.Timedelta(days=i)
                predictions.append({
                    'produit': produit,
                    'date': pred_date,
                    'quantite_estimee': round(mean_daily, 2)
                })

        return predictions

