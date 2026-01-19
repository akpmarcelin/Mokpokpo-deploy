from django.contrib import admin
from .models import (
    Role, Utilisateur, Produit, HistoriquePrix,
    Entrepot, Emplacement, Lot, MouvementStock,
    Livraison, LigneLivraison, PrevisionDemande, Tournee
)


# ====================
# ROLE
# ====================
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)


# ====================
# UTILISATEUR
# ====================
@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'nom',
        'prenom',
        'telephone',
        'email',
        'role',
        'latitude',
        'longitude',
        'actif'
    )

    list_filter = ('role', 'actif')
    search_fields = ('username', 'nom', 'prenom', 'email', 'telephone')
    readonly_fields = ('date_inscription',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {
            'fields': (
                'nom',
                'prenom',
                'email',
                'telephone',
                'latitude',
                'longitude'
            )
        }),
        ('Rôle & rattachement', {
            'fields': ('role', 'entrepot', 'actif')
        }),
        ('Dates', {
            'fields': ('date_inscription',),
            'classes': ('collapse',)
        }),
    )



# ====================
# PRODUIT
# ====================
@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type_produit', 'unite', 'prix_reference')
    list_filter = ('type_produit',)
    search_fields = ('nom',)


# ====================
# HISTORIQUE PRIX
# ====================
@admin.register(HistoriquePrix)
class HistoriquePrixAdmin(admin.ModelAdmin):
    list_display = ('produit', 'prix', 'date')
    list_filter = ('produit', 'date')


# ====================
# ENTREPOT
# ====================
@admin.register(Entrepot)
class EntrepotAdmin(admin.ModelAdmin):
    list_display = ('nom', 'latitude', 'longitude')
    search_fields = ('nom',)


# ====================
# EMPLACEMENT
# ====================
@admin.register(Emplacement)
class EmplacementAdmin(admin.ModelAdmin):
    list_display = ('entrepot', 'code_emplacement')
    list_filter = ('entrepot',)
    search_fields = ('code_emplacement',)


# ====================
# LOT
# ====================
@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = (
        'code_lot', 'produit',
        'quantite_initiale', 'quantite_restante',
        'date_production', 'emplacement'
    )
    list_filter = ('produit', 'emplacement__entrepot')
    search_fields = ('code_lot',)


# ====================
# MOUVEMENT STOCK
# ====================
@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = (
        'lot', 'type_mouvement', 'quantite',
        'source_emplacement', 'destination_emplacement',
        'utilisateur', 'date'
    )
    list_filter = ('type_mouvement', 'date')
    search_fields = ('lot__code_lot',)
    readonly_fields = ('date',)


# ====================
# LIVRAISON
# ====================
@admin.register(Livraison)
class LivraisonAdmin(admin.ModelAdmin):
    list_display = (
        'numero', 'grossiste', 'livreur',
        'entrepot', 'statut',
        'date_livraison', 'date_creation'
    )
    list_filter = ('statut', 'entrepot', 'date_livraison')
    search_fields = ('numero', 'grossiste__username')
    readonly_fields = ('date_creation',)


# ====================
# LIGNE LIVRAISON
# ====================
@admin.register(LigneLivraison)
class LigneLivraisonAdmin(admin.ModelAdmin):
    list_display = ('livraison', 'produit', 'lot', 'quantite')
    list_filter = ('produit',)


# ====================
# PREVISION DEMANDE
# ====================
@admin.register(PrevisionDemande)
class PrevisionDemandeAdmin(admin.ModelAdmin):
    list_display = ('produit', 'periode', 'quantite_prevue', 'date_calcul')
    list_filter = ('produit', 'periode')
    readonly_fields = ('date_calcul',)


# ====================
# TOURNEE LIVREUR
# ====================
@admin.register(Tournee)
class TourneeAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'livreur', 'entrepot', 'distance_totale'
    )
    list_filter = ('entrepot', 'date')
    readonly_fields = ('date',)

