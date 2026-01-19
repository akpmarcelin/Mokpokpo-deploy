import pickle
import numpy as np
import pandas as pd
import os
from pathlib import Path

class MLPredictionService:
    """
    Service de prédiction utilisant les modèles ML entraînés
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.colonnes_attendues = [
            'superficie_totale', 
            'precipitations_mm', 
            'temperature_moyenne',
            'age_plants_moyen', 
            'mois', 
            'cout_intrants'
        ]
        self._load_models()
    
    def _load_models(self):
        """Charger les modèles pickle"""
        try:
            # Utiliser le chemin relatif depuis ce fichier jusqu'à la racine du projet
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            
            model_path = 'ml_models/modele_ventes_cafe_cacao.pkl'
            scaler_path =  'ml_models/scaler.pkl'
            
            print(f"Dossier actuel: {current_dir}")
            print(f"Racine projet: {project_root}")
            print(f"Chemin modèle: {model_path}")
            print(f"Chemin scaler: {scaler_path}")
            print(f"Fichier modèle existe: {model_path.exists()}")
            print(f"Fichier scaler existe: {scaler_path.exists()}")
            
            # Vérifier que les fichiers existent
            if not model_path.exists():
                raise FileNotFoundError(f"Fichier modèle non trouvé: {model_path}")
            if not scaler_path.exists():
                raise FileNotFoundError(f"Fichier scaler non trouvé: {scaler_path}")
            
            # Charger le modèle
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Charger le scaler
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
                
            print(f"✅ Modèles chargés avec succès: {type(self.model)}, {type(self.scaler)}")
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement des modèles: {e}")
            import traceback
            traceback.print_exc()
            self.model = None
            self.scaler = None
    
    def predict(self, data):
        """
        Faire une prédiction avec les données fournies
        
        Args:
            data: dict avec les clés correspondant aux colonnes_attendues
        
        Returns:
            dict: résultat de la prédiction
        """
        if not self.model or not self.scaler:
            return {
                'success': False,
                'error': 'Modèles non chargés',
                'prediction': None
            }
        
        try:
            # Convertir en DataFrame avec les colonnes dans le bon ordre
            df = pd.DataFrame([data], columns=self.colonnes_attendues)
            
            # Normaliser les données
            scaled_data = self.scaler.transform(df)
            
            # Faire la prédiction
            prediction = self.model.predict(scaled_data)[0]
            
            return {
                'success': True,
                'prediction': float(prediction),
                'input_data': data,
                'prediction_rounded': round(float(prediction), 2)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'prediction': None
            }
    
    def predict_multiple(self, data_list):
        """
        Faire plusieurs prédictions
        
        Args:
            data_list: liste de dicts avec les données
        
        Returns:
            list: résultats des prédictions
        """
        results = []
        for data in data_list:
            result = self.predict(data)
            results.append(result)
        return results
    
    def get_feature_info(self):
        """Retourner des informations sur les features attendues"""
        return {
            'colonnes_attendues': self.colonnes_attendues,
            'nombre_features': len(self.colonnes_attendues),
            'description': {
                'superficie_totale': 'Surface totale cultivée (en hectares)',
                'precipitations_mm': 'Précipitations moyennes (en mm)',
                'temperature_moyenne': 'Température moyenne (en °C)',
                'age_plants_moyen': 'Âge moyen des plants (en années)',
                'mois': 'Mois de l\'année (1-12)',
                'cout_intrants': 'Coût des intrants (en FCFA/hectare)'
            }
        }
