from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


# ====================
# ROLE
# ====================
class Role(models.Model):
    nom = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nom


# ====================
# UTILISATEUR
# ====================
class Utilisateur(AbstractUser):
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    role = models.ForeignKey(
        "Role",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    entrepot = models.ForeignKey(
        "Entrepot",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="utilisateurs"
    )

    actif = models.BooleanField(default=True)
    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nom', 'prenom']

    def get_full_name(self):
        full_name = f"{self.prenom} {self.nom}".strip()
        return full_name if full_name else self.username

    def __str__(self):
        return self.get_full_name()


# ====================
# PRODUIT
# ====================
class Produit(models.Model):
    TYPE_CHOICES = [
        ('CAFE', 'Café'),
        ('CACAO', 'Cacao'),
    ]

    nom = models.CharField(max_length=100)
    type_produit = models.CharField(max_length=10, choices=TYPE_CHOICES)
    unite = models.CharField(max_length=20)
    prix_reference = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nom


# ====================
# HISTORIQUE DES PRIX (IA)
# ====================
class HistoriquePrix(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()


# ====================
# ENTREPOT
# ====================
class Entrepot(models.Model):
    nom = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.nom


# ====================
# EMPLACEMENT
# ====================
class Emplacement(models.Model):
    entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE)
    code_emplacement = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.entrepot.nom} - {self.code_emplacement}"


# ====================
# LOT
# ====================
class Lot(models.Model):
    code_lot = models.CharField(max_length=100, unique=True)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite_initiale = models.FloatField()
    quantite_restante = models.FloatField()
    date_production = models.DateField()
    emplacement = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.code_lot


# ====================
# MOUVEMENT DE STOCK
# ====================
class MouvementStock(models.Model):
    TYPE_CHOICES = [
        ('ENTREE', 'Entrée'),
        ('SORTIE', 'Sortie'),
        ('TRANSFERT', 'Transfert'),
    ]

    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name='mouvements')
    type_mouvement = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantite = models.FloatField()

    source_emplacement = models.ForeignKey(
        Emplacement, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='sorties'
    )
    destination_emplacement = models.ForeignKey(
        Emplacement, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='entrees'
    )

    utilisateur = models.ForeignKey(Utilisateur, null=True, on_delete=models.SET_NULL)
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.type_mouvement == 'ENTREE' and self.source_emplacement:
            raise ValidationError("Entrée avec source interdite")
        if self.type_mouvement == 'SORTIE' and self.destination_emplacement:
            raise ValidationError("Sortie avec destination interdite")
        if self.type_mouvement == 'TRANSFERT' and not (self.source_emplacement and self.destination_emplacement):
            raise ValidationError("Transfert incomplet")
        super().save(*args, **kwargs)


# ====================
# LIVRAISON
# ====================
class Livraison(models.Model):
    STATUT_CHOICES = [
        ('PREPARATION', 'Préparation'),
        ('EN_ROUTE', 'En route'),
        ('LIVREE', 'Livrée'),
    ]

    numero = models.CharField(max_length=50, unique=True)

    grossiste = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='commandes'
    )

    livreur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='livraisons'
    )

    entrepot = models.ForeignKey(
        Entrepot,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='PREPARATION'
    )

    date_livraison = models.DateField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.numero


# ====================
# LIGNE LIVRAISON
# ====================
class LigneLivraison(models.Model):
    livraison = models.ForeignKey(Livraison, on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    lot = models.ForeignKey(Lot, null=True, blank=True, on_delete=models.SET_NULL)
    quantite = models.FloatField()


# ====================
# PREVISION DEMANDE (IA)
# ====================
class PrevisionDemande(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    periode = models.CharField(max_length=20)
    quantite_prevue = models.FloatField()
    date_calcul = models.DateTimeField(auto_now_add=True)


# ====================
# TOURNEE (HISTORIQUE)
# ====================
class Tournee(models.Model):
    livreur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    entrepot = models.ForeignKey(Entrepot, on_delete=models.CASCADE)
    date = models.DateField()
    ordre = models.JSONField(help_text="Liste ordonnée des IDs de livraisons")
    distance_totale = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Tournée {self.date} - {self.livreur}"

