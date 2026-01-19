import json
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages

from .models import (
    Utilisateur, Role, Lot, Emplacement, MouvementStock,
    Produit, Livraison, LigneLivraison, Entrepot
)
from .forms import UtilisateurCreationForm

from openrouteservice import Client
from .tsp import solve_tsp
from .utils import haversine
from django.conf import settings
from .utils import entrepot_le_plus_proche



def index(request):
    return render(request, 'index.html')


def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)

        role = user.role.nom if user.role else ''
        if role == 'GROSSISTE':
            return redirect('dashboard_grossiste')
        elif role == 'STOCK':
            return redirect('dashboard_stock')
        elif role == 'GERANT':
            return redirect('dashboard_gerant')
        elif role == 'LIVREUR':
            return redirect('dashboard_livreur')
        else:
            return redirect('index')

    return render(request, 'login.html', {'form': form})


def register_grossiste(request):
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST)

        if form.is_valid():
            role, _ = Role.objects.get_or_create(nom='GROSSISTE')

            user = form.save(commit=False)
            user.role = role
            user.is_active = True
            user.username = user.username.lower()
            user.save()

            login(request, user)
            messages.success(request, "Inscription réussie 🎉")

            return redirect('dashboard_grossiste')
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")

    else:
        form = UtilisateurCreationForm()

    return render(request, 'register.html', {'form': form})

@login_required
def dashboard_stock(request):
    lots = Lot.objects.filter(quantite_restante__gt=0).order_by('-date_production')
    mouvements = MouvementStock.objects.all().order_by('-date')
    emplacements = Emplacement.objects.all()
    produits = Produit.objects.all()
    livraisons = Livraison.objects.filter(statut='PREPARATION').order_by('date_livraison')
    livreurs = Utilisateur.objects.filter(role__nom='LIVREUR', actif=True)
    for livraison in livraisons:
        livraison.entrepot_suggere = entrepot_le_plus_proche(livraison.grossiste)


    return render(request, 'dashboard_stock.html', {
        'lots': lots,
        'mouvements': mouvements,
        'emplacements': emplacements,
        'produits': produits,
        'livraisons': livraisons,
        'livreurs': livreurs,
    })


@login_required
def add_lot(request):
    if request.method == 'POST':
        produit = Produit.objects.get(id=request.POST.get('produit'))
        emplacement = Emplacement.objects.get(id=request.POST.get('emplacement'))
        quantite = float(request.POST.get('quantite'))
        date_prod = request.POST.get('date_production')

        Lot.objects.create(
            code_lot=f"{produit.nom[:3].upper()}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            produit=produit,
            quantite_initiale=quantite,
            quantite_restante=quantite,
            date_production=date_prod,
            emplacement=emplacement
        )
    return redirect('dashboard_stock')


@login_required
def move_lot(request):
    if request.method == 'POST':
        lot = Lot.objects.get(id=request.POST.get('lot'))
        destination = Emplacement.objects.get(id=request.POST.get('destination'))

        MouvementStock.objects.create(
            lot=lot,
            type_mouvement='TRANSFERT',
            quantite=lot.quantite_restante,
            source_emplacement=lot.emplacement,
            destination_emplacement=destination,
            utilisateur=request.user,
            date=timezone.now()
        )
        lot.emplacement = destination
        lot.save()
    return redirect('dashboard_stock')


@login_required
def assign_lot_and_livreur(request, livraison_id, ligne_id):
    if request.method == 'POST':
        try:
            ligne = LigneLivraison.objects.get(id=ligne_id)
            livraison = Livraison.objects.get(id=livraison_id)

            lot_id = request.POST.get('lot')
            quantite_str = request.POST.get('quantite')
            livreur_id = request.POST.get('livreur')

            if not all([lot_id, quantite_str, livreur_id]):
                messages.error(request, "Tous les champs sont obligatoires")
                return redirect('dashboard_stock')

            quantite = float(quantite_str)
            if quantite <= 0:
                raise ValueError("La quantité doit être positive")

            lot = Lot.objects.get(id=lot_id, produit=ligne.produit)
            if lot.quantite_restante < quantite:
                messages.error(request, f"Quantité insuffisante en stock. Il reste {lot.quantite_restante} kg")
                return redirect('dashboard_stock')

            livreur = Utilisateur.objects.get(id=livreur_id, role__nom='LIVREUR')

            ligne.lot = lot
            ligne.quantite = quantite
            ligne.save()

            lot.quantite_restante -= quantite
            lot.save()

            MouvementStock.objects.create(
                lot=lot,
                type_mouvement='SORTIE',
                quantite=quantite,
                source_emplacement=lot.emplacement,
                destination_emplacement=None,
                utilisateur=request.user if request.user.role.nom == "STOCK" else None,
                date=timezone.now()
            )

            livraison.livreur = livreur

            if livraison.entrepot is None and lot.emplacement is not None:
                livraison.entrepot = lot.emplacement.entrepot

            if all(l.lot for l in livraison.lignelivraison_set.all()):
                livraison.statut = 'EN_ROUTE'
            livraison.save()

            messages.success(request, "Lot et livreur affectés avec succès")

        except Exception as e:
            messages.error(request, f"Une erreur est survenue : {str(e)}")

    return redirect('dashboard_stock')


from collections import defaultdict
from django.utils.timezone import localdate

@login_required
def dashboard_livreur(request):
    if request.user.role.nom != "LIVREUR":
        return redirect("index")

    livraisons = Livraison.objects.filter(
        livreur=request.user
    ).select_related("grossiste").order_by("date_livraison")

    groupes = defaultdict(list)
    livrees = []

    for l in livraisons:
        if l.statut == "LIVREE":
            livrees.append(l)
        else:
            groupes[l.date_livraison].append(l)

    groupes_final = []
    for date, lst in groupes.items():
        groupes_final.append({
            "date": date,
            "livraisons": lst,
            "peut_optimiser": len(lst) > 1
        })

    return render(request, "dashboard_livreur.html", {
        "groupes": groupes_final,
        "livraisons_livrees": livrees
    })




@login_required
def livreur_marquer_livree(request, livraison_id):
    if request.method == 'POST':
        livraison = Livraison.objects.get(id=livraison_id, livreur=request.user)
        livraison.statut = 'LIVREE'
        livraison.save()
    return redirect('dashboard_livreur')


@login_required
def grossiste_dashboard(request):
    if not request.user.role or request.user.role.nom != "GROSSISTE":
        return redirect('index')

    produits = Produit.objects.all()
    livraisons = Livraison.objects.filter(grossiste=request.user)

    return render(request, 'dashboard_grossiste.html', {
        'produits': produits,
        'livraisons': livraisons,
    })


@login_required
def pass_order(request):
    if not request.user.role or request.user.role.nom != "GROSSISTE":
        return redirect('index')

    if request.method == 'POST':
        produit_id = request.POST.get('produit')
        quantite = float(request.POST.get('quantite'))
        date_livraison = request.POST.get('date_livraison')
        notes = request.POST.get('notes', '')

        produit = Produit.objects.get(id=produit_id)

        numero = f"LIV-{timezone.now().strftime('%Y%m%d%H%M%S')}"

        livraison = Livraison.objects.create(
            numero=numero,
            grossiste=request.user,
            statut='PREPARATION',
            date_livraison=date_livraison
        )

        LigneLivraison.objects.create(
            livraison=livraison,
            produit=produit,
            quantite=quantite
        )

        return redirect('dashboard_grossiste')

    return redirect('dashboard_grossiste')


@login_required
def dashboard_gerant(request):
    if not request.user.role or request.user.role.nom != "GERANT":
        return redirect('index')

    mouvements = MouvementStock.objects.all().order_by('-date')
    employes = Utilisateur.objects.filter(role__nom__in=['STOCK', 'LIVREUR']).order_by('role', 'nom')

    return render(request, 'dashboard_gerant.html', {
        'mouvements': mouvements,
        'employes': employes
    })


from core.ia.model import StockPredictor
from core.ia.ml_service import MLPredictionService
from core.ia.charts import ChartGenerator
from .forms import MLPredictionForm

@login_required
def gerant_predictions(request):
    if not request.user.role or request.user.role.nom != "GERANT":
        return redirect('index')

    # Initialiser le service ML
    ml_service = MLPredictionService()
    prediction_result = None
    form = MLPredictionForm()
    chart_image = None
    feature_importance_chart = None
    seasonal_chart = None

    # Générer les graphiques d'information
    try:
        feature_importance_chart = ChartGenerator.create_feature_importance_chart()
        seasonal_chart = ChartGenerator.create_seasonal_trend_chart()
    except Exception as e:
        print(f"Erreur lors de la génération des graphiques: {e}")

    if request.method == 'POST':
        form = MLPredictionForm(request.POST)
        if form.is_valid():
            # Préparer les données pour la prédiction
            data = {
                'superficie_totale': form.cleaned_data['superficie_totale'],
                'precipitations_mm': form.cleaned_data['precipitations_mm'],
                'temperature_moyenne': form.cleaned_data['temperature_moyenne'],
                'age_plants_moyen': form.cleaned_data['age_plants_moyen'],
                'mois': form.cleaned_data['mois'],
                'cout_intrants': form.cleaned_data['cout_intrants']
            }
            
            # Faire la prédiction
            prediction_result = ml_service.predict(data)
            
            if prediction_result['success']:
                messages.success(request, f"Prédiction réussie : {prediction_result['prediction_rounded']} tonnes")
                
                # Générer le graphique de prédiction
                try:
                    chart_image = ChartGenerator.create_prediction_chart(prediction_result, data)
                except Exception as e:
                    print(f"Erreur lors de la génération du graphique: {e}")
            else:
                messages.error(request, f"Erreur de prédiction : {prediction_result['error']}")

    # Récupérer les anciennes prédictions pour compatibilité
    predictor = StockPredictor()
    old_predictions = predictor.predict_from_db()

    return render(request, 'gerant_predictions_new.html', {
        'form': form,
        'prediction_result': prediction_result,
        'old_predictions': old_predictions,  # Garder pour compatibilité
        'feature_info': ml_service.get_feature_info(),
        'chart_image': chart_image,
        'feature_importance_chart': feature_importance_chart,
        'seasonal_chart': seasonal_chart
    })


from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from openrouteservice import Client
from collections import defaultdict

@login_required
def optimiser_tournee_livreur(request):
    # Vérifier que l'utilisateur a un rôle et qu'il est bien un LIVREUR
    if not hasattr(request.user, 'role') or not request.user.role or request.user.role.nom != "LIVREUR":
        messages.error(request, "Accès réservé aux livreurs.")
        return redirect("index")

    date_cible = request.GET.get("date", timezone.now().date())

    # 1️⃣ Livraisons du jour
    livraisons = list(
        Livraison.objects.filter(
            livreur=request.user,
            statut__in=["PREPARATION", "EN_ROUTE"],
            date_livraison=date_cible
        ).select_related("grossiste", "entrepot")
    )

    if not livraisons:
        messages.info(request, "Aucune livraison à optimiser pour cette date.")
        return redirect("dashboard_livreur")

    # 2️⃣ Trouver un entrepôt valide
    entrepot = None

    for l in livraisons:
        if l.entrepot and l.entrepot.latitude and l.entrepot.longitude:
            entrepot = l.entrepot
            break

    if entrepot is None:
        messages.error(request, "Aucun entrepôt valide avec coordonnées.")
        return redirect("dashboard_livreur")

    # 3️⃣ Livraisons avec coordonnées valides
    livraisons_valides = [
        l for l in livraisons
        if l.grossiste.latitude and l.grossiste.longitude
    ]

    if len(livraisons_valides) < 2:
        messages.info(request, "Pas assez de livraisons avec coordonnées pour optimiser.")
        return redirect("dashboard_livreur")

    # 4️⃣ Coordonnées ORS (entrepôt + clients)
    coords = [(entrepot.longitude, entrepot.latitude)]
    for l in livraisons_valides:
        coords.append((l.grossiste.longitude, l.grossiste.latitude))

    # 5️⃣ ORS : matrice de distance
    client = Client(key=settings.ORS_API_KEY)
    matrix = client.distance_matrix(
        locations=coords,
        metrics=["distance"],
        profile="driving-car"
    )

    distances = matrix["distances"]

    # 6️⃣ TSP (ordre optimal)
    ordre = solve_tsp(distances)

    # 7️⃣ Distance totale
    dist_total = 0
    for i in range(len(ordre) - 1):
        dist_total += distances[ordre[i]][ordre[i + 1]]

    # 8️⃣ Ordre des livraisons (sans l’entrepôt)
    ordre_livraisons = [
        livraisons_valides[i - 1].id
        for i in ordre if i != 0
    ]

    # 9️⃣ Étapes POUR LEAFLET (IMPORTANT)
    etapes = []
    
    # Obtenir l'itinéraire complet
    coordinates = []
    for i in range(len(ordre)):
        if i == 0:  # Entrepôt
            coordinates.append([entrepot.longitude, entrepot.latitude])
        else:  # Points de livraison
            liv = livraisons_valides[ordre[i] - 1]
            coordinates.append([liv.grossiste.longitude, liv.grossiste.latitude])
    
    # Obtenir l'itinéraire détaillé depuis OpenRouteService
    try:
        ors_client = Client(key=settings.ORS_API_KEY)
        route = ors_client.directions(
            coordinates=coordinates,
            profile='driving-car',
            format='geojson',
            optimize_waypoints=True
        )
        
        # Ajouter la géométrie de l'itinéraire aux données de session
        route_geometry = route['features'][0]['geometry']
    except Exception as e:
        print(f"Erreur lors de la récupération de l'itinéraire: {e}")
        route_geometry = None
    
    # Préparer les étapes avec les informations de l'itinéraire
    for i in range(1, len(ordre)):
        idx_cur = ordre[i]
        liv = livraisons_valides[idx_cur - 1]
        
        etapes.append({
            "livraison_id": liv.id,
            "grossiste": liv.grossiste.get_full_name() or liv.grossiste.username,
            "latitude": float(liv.grossiste.latitude),
            "longitude": float(liv.grossiste.longitude),
            "distance_depuis_precedent": round(distances[ordre[i-1]][idx_cur] / 1000, 2),
            "entrepot_latitude": float(entrepot.latitude),
            "entrepot_longitude": float(entrepot.longitude),
            "entrepot_nom": entrepot.nom
        })
    
    # Ajouter la géométrie de l'itinéraire aux données de session
    if route_geometry:
        request.session["route_geometry"] = route_geometry

    # 🔐 Sauvegarde session
    request.session["ordre_livraisons"] = ordre_livraisons
    request.session["date_optimisation"] = str(date_cible)
    request.session["distance_totale"] = round(dist_total / 1000, 2)
    request.session["etapes_tournee"] = etapes

    return redirect("detail_tournee")


@login_required
def detail_tournee(request):
    # Vérifier que l'utilisateur a un rôle et qu'il est bien un LIVREUR
    if not hasattr(request.user, 'role') or not request.user.role or request.user.role.nom != "LIVREUR":
        messages.error(request, "Accès réservé aux livreurs.")
        return redirect("index")
    
    # Récupérer les données de la session
    date_optimisation = request.session.get("date_optimisation")
    distance_totale = request.session.get("distance_totale")
    etapes = request.session.get("etapes_tournee", [])
    
    # Vérifier si les données nécessaires sont présentes
    if not all([date_optimisation, distance_totale is not None, etapes]):
        messages.error(request, "Aucun itinéraire optimisé trouvé. Veuillez d'abord optimiser une tournée.")
        return redirect("dashboard_livreur")
    
    # Nettoyer les étapes pour s'assurer que les coordonnées sont valides
    etapes_valides = []
    for etape in etapes:
        try:
            # Convertir en float et vérifier que les coordonnées sont des nombres valides
            lat = float(etape.get('latitude', 0))
            lon = float(etape.get('longitude', 0))
            entrepot_lat = float(etape.get('entrepot_latitude', 0))
            entrepot_lon = float(etape.get('entrepot_longitude', 0))
            
            if lat == 0 or lon == 0:
                continue
                
            etape['latitude'] = lat
            etape['longitude'] = lon
            etape['entrepot_latitude'] = entrepot_lat
            etape['entrepot_longitude'] = entrepot_lon
            
            etapes_valides.append(etape)
        except (TypeError, ValueError):
            continue
    
    if not etapes_valides:
        messages.error(request, "Aucun point de livraison valide avec des coordonnées géographiques.")
        return redirect("dashboard_livreur")
    
    # Récupérer et formater la géométrie de l'itinéraire depuis la session
    route_geometry = request.session.get("route_geometry")
    route_geometry_json = json.dumps(route_geometry) if route_geometry else None
    
    return render(request, "detail_tournee.html", {
        "date": date_optimisation,
        "distance_totale": distance_totale,
        "etapes": etapes_valides,
        "has_etapes": len(etapes_valides) > 0,
        "route_geometry_json": route_geometry_json
    })

