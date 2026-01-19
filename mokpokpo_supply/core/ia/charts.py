# import matplotlib.pyplot as plt
# import matplotlib
# matplotlib.use('Agg')  # Mode non-interactif pour Django
# import numpy as np
# import io
# import base64
# from django.conf import settings

class ChartGenerator:
    """Générateur de graphiques pour les prédictions ML"""
    
    @staticmethod
    def create_prediction_chart(prediction_result, input_data):
        """
        Créer un graphique pour visualiser la prédiction
        
        Args:
            prediction_result: dict avec le résultat de prédiction
            input_data: dict avec les données d'entrée
        
        Returns:
            str: image encodée en base64
        """
        # Temporairement désactivé en attendant matplotlib
        return None
    
    @staticmethod
    def create_feature_importance_chart():
        """
        Créer un graphique montrant l'importance des features
        
        Returns:
            str: image encodée en base64
        """
        # Temporairement désactivé en attendant matplotlib
        return None
    
    @staticmethod
    def create_seasonal_trend_chart():
        """
        Créer un graphique des tendances saisonnières
        
        Returns:
            str: image encodée en base64
        """
        # Temporairement désactivé en attendant matplotlib
        return None
