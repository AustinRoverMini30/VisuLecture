# Modifications effectuées : Support des enregistrements multiples par élève

## Résumé
Le système a été modifié pour permettre à un élève d'avoir plusieurs enregistrements de lecture, au lieu d'être limité à un seul texte.

## Modifications de la structure de données

### Nouveaux modèles
1. **Reading.cs** (nouveau fichier)
   - Représente un enregistrement de lecture
   - Propriétés :
     - `Id` : Identifiant unique de la lecture
     - `Date` : Date et heure de l'enregistrement
     - `StudentId` : ID de l'étudiant
     - `TextId` : ID du texte lu
     - Relations de navigation vers `Student` et `TextRecord`

### Modifications du modèle Student
- **Supprimé** : Propriété `TextId` (un étudiant ne stocke plus directement un texte)
- **Ajouté** : Collection `Readings` (ICollection<Reading>)
- Le constructeur a été adapté pour ne plus accepter `textId`

### Base de données
- **Nouvelle table** : `Readings`
  - Clé étrangère vers `Students` (CASCADE DELETE)
  - Clé étrangère vers `TextRecords` (RESTRICT DELETE)
- **Migration** : `20251231120000_InitialCreate.cs`

## Modifications de l'interface utilisateur

### TeacherPanel.razor
- Le bouton "Consulter" affiche maintenant le nombre d'enregistrements : "Consulter (N)"
- Si l'élève a plusieurs enregistrements, un dialog s'ouvre pour choisir lequel consulter
- Si l'élève n'a aucun enregistrement, le bouton "Consulter" n'apparaît pas
- Nouvelle méthode `ShowReadings()` qui remplace `Open()`

### ReadingSelector.razor (nouveau composant)
- Dialog permettant de sélectionner un enregistrement parmi plusieurs
- Affiche la date et le texte de chaque enregistrement
- Interface intuitive avec des cartes cliquables

### ShowData.razor
- Le paramètre de route change : `/show-data/{readingId}` au lieu de `/show-data/{idReader}`
- Charge les données à partir de l'ID de lecture (Reading) au lieu de l'ID de l'étudiant
- Les fichiers CSV sont maintenant stockés dans `records/{readingId}/` au lieu de `records/{studentId}/`

### ReadingProcess.razor
- Nouveau champ `readingId` pour stocker l'ID de la lecture en cours
- La méthode `SelectText()` crée maintenant un enregistrement `Reading` dans la base
- Toutes les références à `calibrationId` utilisent maintenant `readingId`
- Les vidéos et données sont maintenant associées à l'ID de lecture

### StudentModifier.razor
- Le constructeur `Student` ne nécessite plus le paramètre `TextId`

## Modifications JavaScript

### record.js
- `startRecording()` : Utilise `readingId` au lieu de `calibrationIndex`
- `uploadVideo(readingId)` : Accepte maintenant `readingId` en paramètre
- `uploadVideo2(readingId)` : Accepte maintenant `readingId` en paramètre
- Les cookies de calibration ne sont plus utilisés

## Flux d'utilisation mis à jour

### Création d'un enregistrement
1. L'utilisateur sélectionne un étudiant
2. L'utilisateur sélectionne un texte
3. **Un enregistrement `Reading` est créé immédiatement** avec un ID unique
4. Cet ID est utilisé tout au long du processus (calibration, enregistrement, stockage)
5. Les vidéos et fichiers CSV sont stockés dans `uploads/{readingId}/` et `records/{readingId}/`

### Consultation d'un enregistrement
1. Dans le panneau enseignant, cliquer sur "Consulter (N)" pour un élève
2. Si N > 1 : Un dialog s'ouvre avec la liste des enregistrements (date + texte)
3. Si N = 1 : Ouvre directement l'enregistrement
4. L'affichage utilise l'ID de lecture pour charger les bonnes données

## Avantages
- ✅ Un élève peut maintenant lire plusieurs textes
- ✅ Historique complet des lectures par élève
- ✅ Meilleure traçabilité avec les dates d'enregistrement
- ✅ Structure de données plus flexible et évolutive
- ✅ Pas de conflits entre les enregistrements
- ✅ Conservation de tous les enregistrements précédents

## Notes importantes
- La base de données doit être supprimée et recréée au démarrage (migration automatique activée dans Program.cs)
- Les anciens enregistrements avec `student.TextId` ne sont pas compatibles
- Tous les dossiers `uploads/` et `records/` utilisent maintenant l'ID de lecture au lieu de l'ID de l'étudiant

