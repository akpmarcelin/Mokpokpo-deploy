import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

from .models import Entrepot

def entrepot_le_plus_proche(utilisateur):
    if utilisateur.latitude is None or utilisateur.longitude is None:
        return None

    entrepots = Entrepot.objects.filter(latitude__isnull=False, longitude__isnull=False)

    meilleur = None
    distance_min = float('inf')

    for e in entrepots:
        d = haversine(
            utilisateur.latitude,
            utilisateur.longitude,
            e.latitude,
            e.longitude
        )
        if d < distance_min:
            distance_min = d
            meilleur = e

    return meilleur

