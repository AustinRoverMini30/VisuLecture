# VisuLecture - Guide de démarrage

## Méthodes pour lancer l'application

### Méthode 1 : Depuis Visual Studio / Rider (Recommandé pour le développement)
1. Ouvrir le projet dans l'IDE
2. Appuyer sur F5 ou cliquer sur "Run"

### Méthode 2 : Avec dotnet run (Recommandé)
1. Ouvrir un terminal dans le dossier `VisuLecture\VisuLecture`
2. Exécuter : `dotnet run`
3. L'application sera accessible à : http://localhost:5188

OU double-cliquer sur `StartApp.bat` dans le dossier `VisuLecture\VisuLecture`

### Méthode 3 : Depuis l'exécutable compilé
1. Compiler le projet : `dotnet build`
2. Double-cliquer sur `StartAppFromBin.bat` dans le dossier `VisuLecture\VisuLecture`
3. OU naviguer vers `VisuLecture\VisuLecture\bin\Debug\net9.0` et exécuter `VisuLecture.exe`

### Méthode 4 : Publication pour déploiement
Pour créer une version publiée avec tous les fichiers :
```
cd VisuLecture\VisuLecture
dotnet publish -c Release -o bin\publish
```
Ensuite, tous les fichiers nécessaires seront dans `bin\publish` et vous pouvez exécuter `VisuLecture.exe` depuis ce dossier.

## Dépannage

### Les fichiers JavaScript ne se chargent pas
- Vérifiez que le dossier `wwwroot` est présent à côté de l'exécutable
- Si vous exécutez depuis `bin\Debug\net9.0`, assurez-vous que le dossier `wwwroot` y est bien présent
- Recompilez le projet : `dotnet build`

### La police Eurostile ne se charge pas
- Vérifiez que le fichier `wwwroot/fonts/fonnts.com-Eurostile_Black.otf` existe
- Si le problème persiste, vérifiez les erreurs dans la console du navigateur (F12)

### L'application ne démarre pas
- Vérifiez que le port 5188 n'est pas déjà utilisé
- Vérifiez que vous avez les permissions nécessaires pour lancer un serveur web
- Assurez-vous que .NET 9.0 est installé

## Configuration

L'application écoute sur toutes les interfaces réseau (0.0.0.0:5188) pour permettre l'accès depuis d'autres machines du réseau local.

Pour changer le port, modifiez la ligne suivante dans `Program.cs` :
```csharp
builder.WebHost.UseUrls("http://0.0.0.0:5188");
```

## Notes importantes

- **Ne fermez pas la fenêtre de terminal** tant que vous utilisez l'application
- Les fichiers de la base de données SQLite sont stockés dans `app.db`
- Les enregistrements sont stockés dans les dossiers `records` et `uploads`
- Les images de textes OCR sont dans `wwwroot/textImg`

