# Système de Thèmes pour la Calibration

## Vue d'ensemble

Le système de thèmes permet de remplacer les ronds blancs utilisés pendant la calibration par des images thématiques adaptées aux préférences de l'élève.

## Thèmes disponibles

### 1. Défaut (Theme = 1)
- Affiche des ronds blancs classiques
- Aucune image nécessaire

### 2. Pompier (Theme = 2)
- Affiche des images sur le thème des pompiers
- Dossier : `pictures/themes/pompier/`
- Images requises :
  - `pompier.png` (position centre)
  - `pompier1.png` (coin supérieur gauche)
  - `pompier2.png` (coin supérieur droit)
  - `pompier3.png` (coin inférieur droit)
  - `pompier4.png` (coin inférieur gauche)

### 3. Planète (Theme = 3)
- Affiche des images de planètes
- Dossier : `pictures/themes/planets/`
- Images requises :
  - `planet.png` (position centre)
  - `planet1.png` (coin supérieur gauche)
  - `planet2.png` (coin supérieur droit)
  - `planet3.png` (coin inférieur droit)
  - `planet4.png` (coin inférieur gauche)

## Comment ajouter un nouveau thème

1. Créer un nouveau dossier dans `wwwroot/pictures/themes/{nom_du_theme}/`
2. Ajouter 5 images PNG (avec ou sans transparence) :
   - `{theme}.png`
   - `{theme}1.png`
   - `{theme}2.png`
   - `{theme}3.png`
   - `{theme}4.png`
3. Modifier le fichier `ReadingProcess.razor` :
   - Ajouter une option dans le RadioButtonList (ligne ~176)
   - Mettre à jour la méthode `GetThemeName()` pour inclure le nouveau thème
   - Mettre à jour la méthode `GetThemeImagePath()` pour gérer les chemins des nouvelles images

## Spécifications techniques

- **Format recommandé** : PNG avec transparence
- **Taille** : Les images seront automatiquement redimensionnées à 50x50 pixels (variable `dotW`)
- **Positions** : Les images sont affichées à 5 positions fixes pendant la calibration :
  0. Centre de l'écran
  1. Coin supérieur gauche
  2. Coin supérieur droit
  3. Coin inférieur droit
  4. Coin inférieur gauche

## Implémentation

Le système utilise :
- Le champ `Theme` dans le modèle `Student` (valeur int : 1, 2, 3, etc.)
- La méthode `GetThemeName()` pour convertir l'ID en nom de thème
- La méthode `GetThemeImagePath()` pour générer le chemin de l'image en fonction de la position actuelle
- Un bloc conditionnel dans le HTML pour afficher soit un rond blanc, soit une image

## Exemples d'utilisation

### Élève avec thème Planète
```csharp
var student = new Student
{
    FirstName = "Marie",
    LastName = "Dupont",
    Theme = 3  // Planète
};
```
→ Les images `planet.png`, `planet1.png`, etc. seront affichées pendant la calibration

### Élève avec thème Défaut
```csharp
var student = new Student
{
    FirstName = "Jean",
    LastName = "Martin",
    Theme = 1  // Défaut
};
```
→ Des ronds blancs classiques seront affichés pendant la calibration

