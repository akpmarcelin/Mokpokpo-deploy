#!/usr/bin/env python3
import os
from pathlib import Path

# Test pour trouver les bons chemins
print("=== Test des chemins des modèles ===")

# Chemin actuel du script
current_file = Path(__file__).resolve()
print(f"Fichier actuel: {current_file}")

# Dossier core/ia/
core_ia_dir = current_file.parent
print(f"Dossier core/ia: {core_ia_dir}")

# Dossier core/
core_dir = core_ia_dir.parent
print(f"Dossier core: {core_dir}")

# Dossier mokpokpo_supply/
mokpokpo_dir = core_dir.parent
print(f"Dossier mokpokpo_supply: {mokpokpo_dir}")

# Racine du projet
project_root = mokpokpo_dir.parent
print(f"Racine du projet: {project_root}")

# Chemins possibles pour les modèles
possible_model_paths = [
    project_root / 'ml_models' / 'modele_ventes_cafe_cacao.pkl',
    mokpokpo_dir / 'ml_models' / 'modele_ventes_cafe_cacao.pkl',
    core_ia_dir / 'modele_ventes_cafe_cacao.pkl',
]

possible_scaler_paths = [
    project_root / 'ml_models' / 'scaler.pkl',
    mokpokpo_dir / 'ml_models' / 'scaler.pkl',
    core_ia_dir / 'scaler.pkl',
]

print("\n=== Test des chemins possibles ===")
for i, (model_path, scaler_path) in enumerate(zip(possible_model_paths, possible_scaler_paths)):
    print(f"\nOption {i+1}:")
    print(f"  Modèle: {model_path}")
    print(f"  Existe: {model_path.exists()}")
    print(f"  Scaler: {scaler_path}")
    print(f"  Existe: {scaler_path.exists()}")

# Si on trouve les fichiers, tester de les charger
for i, (model_path, scaler_path) in enumerate(zip(possible_model_paths, possible_scaler_paths)):
    if model_path.exists() and scaler_path.exists():
        print(f"\n=== Test de chargement Option {i+1} ===")
        try:
            import pickle
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            print(f"Modèle chargé: {type(model)}")
            
            with open(scaler_path, 'rb') as f:
                scaler = pickle.load(f)
            print(f"Scaler chargé: {type(scaler)}")
            print("✅ Succès !")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
