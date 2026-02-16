# Instagram Image Downloader

Télécharge les images d'un compte Instagram public ou privé (avec authentification).

## Fonctionnalités

- Téléchargement des dernières images d'un profil Instagram
- Support des comptes publics et privés
- Sauvegarde automatique de la session (pas besoin de se reconnecter)
- Deux méthodes disponibles : Playwright (recommandé) ou Instaloader

## Installation

### 1. Créer un environnement virtuel (recommandé)

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 2. Installer les dépendances

```powershell
pip install -r requirements.txt
```

### 3. Installer Playwright (pour scraper_playwright.py)

```powershell
pip install playwright
playwright install firefox
```

## Utilisation

### Méthode 1: Playwright (RECOMMANDÉ)

Activer venv: 
venv\Scripts\Activate

Utilise un vrai navigateur Firefox pour éviter les limitations de l'API Instagram.

```powershell
python scraper_playwright.py
```

**Première utilisation:**
1. Le script ouvre Firefox automatiquement
2. Connectez-vous manuellement à Instagram dans le navigateur
3. Appuyez sur Entrée dans le terminal pour continuer
4. La session est sauvegardée automatiquement dans `instagram_session.json`

**Utilisations suivantes:**
- La session est chargée automatiquement
- Plus besoin de se reconnecter!

**Pour réinitialiser la session:**
```powershell
del instagram_session.json
```

### Méthode 2: Instaloader (peut rencontrer des limitations)

Utilise l'API Instagram via la bibliothèque Instaloader.

#### Option A: Sans authentification (profils publics uniquement)

```powershell
python main.py
```

**Note:** Cette méthode peut rencontrer des erreurs 429 (Too Many Requests) en raison des limitations de l'API Instagram.

#### Option B: Avec authentification (recommandé pour éviter les limitations)

**Étape 1: Importer votre session Firefox**

1. Connectez-vous à Instagram dans Firefox
2. Fermez complètement Firefox
3. Exécutez:

```powershell
python import_session.py
```

**Étape 2: Utiliser la session avec main.py**

```powershell
$env:INSTA_USER="votre_nom_utilisateur_instagram"
python main.py
```

## Structure du projet

```
insta_scrapper/
├── scraper_playwright.py   # Scraper avec navigateur (recommandé)
├── main.py                  # Scraper avec Instaloader
├── import_session.py        # Import de session depuis Firefox
├── requirements.txt         # Dépendances Python
├── instagram_session.json   # Session Playwright (créé après première connexion)
└── downloads/              # Dossier de destination des images
```

## Dépendances

- `instaloader>=4.10` - API Instagram
- `requests>=2.31.0` - Téléchargement HTTP
- `playwright` - Automatisation de navigateur

## Résolution de problèmes

### Erreur 429 (Too Many Requests)

Si vous rencontrez cette erreur avec `main.py`:
1. Utilisez `scraper_playwright.py` à la place (recommandé)
2. Ou attendez 30 minutes avant de réessayer
3. Ou utilisez une session authentifiée via `import_session.py`

### Session expirée

Si la session Playwright expire:
1. Supprimez `instagram_session.json`
2. Relancez le script et reconnectez-vous

### Firefox ne se lance pas

Assurez-vous d'avoir installé Firefox via Playwright:
```powershell
playwright install firefox
```

## Limitations

- Instagram impose des limites de taux (rate limiting)
- Les comptes privés nécessitent une authentification
- Le téléchargement de vidéos est désactivé par défaut

## Avertissement

Ce projet est à des fins éducatives uniquement. Respectez les conditions d'utilisation d'Instagram et la vie privée des utilisateurs.
