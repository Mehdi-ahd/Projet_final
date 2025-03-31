# Documentation du Projet : Explorateur de Fichiers avec Tkinter

## Fonctionnalités Implémentées

### 1. Interface Graphique et Navigation
- **Barre de chemin interactive** : Affiche le chemin actuel avec des boutons cliquables pour chaque segment du chemin (implémentée via `update_path_display()` et `switch_to_entry()`).
- **Navigation hiérarchique** : Double-clic sur un dossier pour y accéder, boutons Retour/Suivant (`go_back()`, `go_ahead()`).
- **Affichage des icônes** : Utilisation de Font Awesome pour les icônes de dossiers (📁) et fichiers (📄).

### 2. Gestion des Favoris et Récents
- **Marquage des favoris** : Ajout/suppression via le menu contextuel (`add_to_favorites()`, `delete_favorites()`).
- **Affichage des favoris** : Section dédiée avec accès direct aux éléments (`show_favorites()`).
- **Historique récent** : Enregistrement automatique des fichiers ouverts (`add_to_recents()`) et suppression automatique au bout de 24 heures.
- **Utilisation de base de données pour le stockage durable des sélections**: Une base données est utilisée pour stockée tous les éléments marqués favoris et les éléments récents.

### 3. Opérations sur les Fichiers
- **Menu contextuel** : Options spécifiques selon le contexte (clic sur un élément vs espace vide) :
  - **Élément sélectionné** : Ouvrir, Renommer, Copier/Coller, Supprimer (`show_item_menu()`).
  - **Espace vide** : Création de dossiers/fichiers (`show_space_menu()`).
- **Calcul de taille** : Affichage asynchrone des propriétés des fichiers/dossiers (`show_properties()`).

### 4. Fonctionnalités Avancées
- **Filtrage des fichiers** : Par type (images, documents, etc.) via `apply_filter()`.
- **Recherche instantanée** : Barre de recherche dynamique (`update_search()`).
- **Mise à jour automatique des repertoires et bouton de rafraichissement**: Les répertoires sont automatiquement mis à jour après des modifcations et possibilité d'actualiser manuellemnt les repertoires avec le bouton de rafraichissement
- **Gestion des erreurs** : Messages clairs pour les accès refusés ou chemins invalides.
  

## Problèmes Rencontrés et Solutions

### 1. Gestion des Chemins d'Accès
**Problème** :  
La permutation entre l'affichage du chemin cliquable et un champ de saisie manuelle était complexe à synchroniser.  
**Solution** :  
- Utilisation de `switch_to_entry()` pour basculer vers un champ de saisie au clic.
- Mise à jour automatique via `load_directory()` après validation.

### 2. Icônes et Police FontAwesome
**Problème** :  
L'affichage des icônes nécessitait une police externe, ce qui pouvait causer des erreurs si non installée.  
**Solution** :  
- Vérification de la présence de la police au démarrage (`font.nametofont("FA")`).
- Fallback vers des caractères Unicode standards si la police est absente.

### 3. Menus Contextuels Dynamiques
**Problème** :  
Distinguer un clic droit sur un élément vs un espace vide pour afficher le bon menu.  
**Solution** :  
- Détection de la position via `file_list.bbox()` dans `right_click()`.
- Affichage conditionnel de `show_item_menu()` ou `show_space_menu()`.

### 4. Calcul de Taille des Dossiers
**Problème** :  
Le calcul récursif de la taille des dossiers bloquait l'interface.  
**Solution** :  
- Implémentation asynchrone avec `threading` dans `show_properties()`.
- Annulation possible via `cancel_event`.

### 5. Synchronisation Base de Données/Fichiers
**Problème** :  
Les favoris pouvaient référencer des fichiers supprimés.  
**Solution** :  
- Nettoyage automatique dans `show_favorites()` et `show_recents()` via `os.path.exists()`.
- Suppression en cascade lors de la suppression de fichiers (`delete_selected_items()`).

---

## Captures d'Écran (Exemples)
1. **Navigation Standard**  
     ![img1](https://github.com/user-attachments/assets/7f72e9ce-5227-4dbb-85c0-2139c1a4c8b2)
     ![img2](https://github.com/user-attachments/assets/9fc20a87-30d6-4b9e-af29-2ae6855ae6de)

   *Barre de chemin, liste des fichiers, et boutons de navigation et adaptabilité des frames à la taille de la fenetre.*

2. **Menu Contextuel**  
   ![img4](https://github.com/user-attachments/assets/c814ce19-45f9-42a3-bc77-1d262bd24fe8)
   *Options pour un fichier sélectionné (Ouvrir, Renommer, etc.).*
   ![img3](https://github.com/user-attachments/assets/9731b36a-05c8-46b7-aa3d-e363ffed844d)
   *Options pour la création de nouveaux éléments et de collage après une copie ou un déplacement.*
   ![img6](https://github.com/user-attachments/assets/bab95f19-ab6d-46f0-86ca-246bdc80f023)
   *Options pour un fichier sélectionné dans le menu favoris.*
   
4. **Gestion des Favoris**  
     ![img7](https://github.com/user-attachments/assets/fde7ce0e-4497-4524-8bc1-b37f6207ae69)

   *Liste des éléments marqués comme favoris et autres sections(recents et dossier racine computer).*
5. **Gestion des Filtres**
   ![img5](https://github.com/user-attachments/assets/042146f0-a108-4824-ad26-7a63f6bc9491)

## Conclusion
Plusieurs défis techniques ont été rencontrés, notamment la gestion des événements complexes et l'intégration de polices externes. Les solutions adoptées garantissent une interface réactive et intuitive, conformément aux spécifications du projet. Les fonctionnalités clés comme les favoris, la recherche, et les menus contextuels dynamiques ont été particulièrement optimisées pour l'expérience utilisateur.

**Prochaines améliorations possibles** :  
- Ajout d'un système d'onglets pour naviguer dans plusieurs dossiers simultanément.
- Intégration d'un lecteur de prévisualisation pour les fichiers multimédias.


