# GreenSentinel
**Système professionnel de surveillance et protection des forêts avec détection intelligente d'incendies**

---

GreenSentinel est une solution complète de surveillance des forêts, combinant une interface web moderne, l'IA (YOLOv8), et la gestion collaborative des alertes pour prévenir les incendies et protéger l'environnement.

---

## Fonctionnalités principales
- Interface web responsive et professionnelle (Bootstrap)
- Tableau de bord avec mission et statistiques en temps réel
- Connexion à des flux vidéo locaux (caméra) ou distants (RTSP)
- Détection d'incendies en temps réel via YOLOv8
- Contrôles pour démarrer/arrêter la surveillance vidéo
- Système d'alertes citoyennes et gestion des statuts (nouvelle, en traitement, résolue)
- Visualisation des images, vidéos et statistiques

---

## Architecture du projet

```
GreenSentinel/
│
├── static/                        # Fichiers statiques (frontend)
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── forest_protection.js
│   │   └── monitoring.js
│   └── img/
│       ├── forest-bg.jpg
│       └── forest-placeholder.jpg
│
├── templates/                     # Templates HTML (Jinja2)
│   ├── admin/
│   │   └── alerts.html
│   ├── alerts.html
│   ├── base.html
│   ├── dashboard.html
│   ├── forest_protection.html
│   ├── monitoring.html
│   └── submit_alert.html
│
├── alerts.db                      # Base de données SQLite des alertes
├── forest_protection_server.py    # Serveur Flask principal
├── last.pt                        # Modèle YOLOv8 entraîné pour la détection d'incendies
├── README.md                      # Documentation générale
└── README_FOREST_PROTECTION.md    # Documentation détaillée du module
```

---

## Prérequis
- Python 3.8 ou supérieur
- Flask
- OpenCV
- Ultralytics YOLOv8
- Bootstrap (via CDN ou local)
- SQLite (intégré)

---

## Installation
1. Clonez le dépôt et placez-vous dans le dossier du projet.
2. Installez les dépendances :
   ```bash
   pip install -r requirements_forest.txt
   ```
3. Placez le modèle YOLOv8 (`last.pt`) à la racine du projet.

---

##  Lancement
```bash
python forest_protection_server.py
```
Puis ouvrez [http://localhost:5000](http://localhost:5000) dans votre navigateur.

---

## Description des principaux fichiers
- **forest_protection_server.py** : Backend Flask, gestion du streaming vidéo, détection IA, endpoints API, gestion des alertes
- **static/** : Fichiers statiques (CSS, JS, images)
- **templates/** : Pages HTML pour l’UI (utilise Jinja2)
- **alerts.db** : Base SQLite pour stocker les alertes
- **last.pt** : Modèle YOLOv8 pour la détection d’incendies
- **README.md / README_FOREST_PROTECTION.md** : Documentation utilisateur et technique

---

## Contribution & Support
- Pour toute suggestion, bug ou contribution, ouvrez une issue ou une pull request sur le dépôt.
- Contact : [Votre Email ou lien GitHub]

---

> **GreenSentinel** : Protégeons nos forêts grâce à l’IA et à l’engagement citoyen 🌳🔥

- Python 3.8 ou supérieur
- OpenCV
- Flask
- Ultralytics YOLOv8
- Un modèle YOLOv8 entraîné pour la détection d'incendies

## Installation

1. Installez les dépendances requises :

```bash
pip install -r requirements.txt
```

2. Assurez-vous que le modèle YOLOv8 (`last.pt`) est présent dans le répertoire du projet, ou modifiez la variable `MODEL_PATH` dans `forest_protection_server.py`.

## Utilisation

1. Lancez le serveur Flask :

```bash
python forest_protection_server.py
```

2. Ouvrez votre navigateur et accédez à l'adresse suivante :

```
http://localhost:5000
```

3. Navigation dans l'interface GreenSentinel :
   - **Tableau de Bord** : Page d'accueil avec la mission du projet, une citation inspirante et les statistiques générales
   - **Surveillance Vidéo** : Page pour connecter et contrôler les flux vidéo avec détection d'incendies
   - **Alertes Citoyennes** : Page pour signaler et gérer les alertes d'incendies

4. Utilisation de la surveillance vidéo :
   - Pour utiliser la caméra locale, laissez "0" dans le champ source
   - Pour utiliser un flux RTSP, entrez l'URL complète (ex: rtsp://utilisateur:mot_de_passe@ip:port/chemin)
   - Cliquez sur "Démarrer" pour lancer la surveillance
   - Cliquez sur "Arrêter" pour mettre fin à la session
   
5. Utilisation des alertes citoyennes :
   - Remplissez le formulaire avec votre nom, la localisation et une description
   - Ajoutez une image optionnelle
   - Soumettez l'alerte qui sera visible dans la liste des alertes récentes
   - Les administrateurs peuvent changer le statut des alertes

## Configuration pour Raspberry Pi

Pour déployer cette application sur une Raspberry Pi :

1. Assurez-vous que la Raspberry Pi dispose d'une caméra connectée ou d'un accès à un flux vidéo
2. Installez les dépendances requises
3. Lancez le serveur avec l'option host pour permettre l'accès depuis d'autres appareils du réseau :

```bash
python forest_protection_server.py
```

L'application sera accessible à l'adresse IP de votre Raspberry Pi sur le port 5000.

## Structure des fichiers

```
heart_failure_prediction/
│
├── forest_protection_server.py         # Serveur Flask principal
├── requirements_forest.txt             # Dépendances spécifiques à ce module
│
├── templates/
│   ├── admin/
│   │   └── alerts.html
│   ├── alerts.html
│   ├── base.html
│   ├── dashboard.html
│   ├── forest_protection.html
│   ├── monitoring.html
│   └── submit_alert.html
│
├── static/
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── forest_protection.js
│   │   └── monitoring.js
│   └── img/
│       ├── forest-bg.jpg
│       └── forest-placeholder.jpg
│
├── models/
│   └── last.pt                        # Modèle YOLOv8 entraîné
│
├── README_FOREST_PROTECTION.md        # Documentation détaillée (ce fichier)
└── ...
```

### Détail des principaux fichiers et dossiers

- `forest_protection_server.py` : Serveur Flask principal, logique backend, endpoints, streaming vidéo, intégration YOLOv8.
- `requirements_forest.txt` : Dépendances nécessaires pour ce projet.
- `templates/` : Pages HTML de l'application (voir détail ci-dessus).
- `static/css/styles.css` : Feuilles de style personnalisées.
- `static/js/forest_protection.js`, `monitoring.js` : Scripts JS pour l’UI et le monitoring.
- `static/img/forest-bg.jpg`, `forest-placeholder.jpg` : Images d’illustration.
- `models/last.pt` : Modèle YOLOv8 pour la détection d’incendies.
- `README_FOREST_PROTECTION.md` : Documentation détaillée du système.

N'hésitez pas à adapter cette structure selon vos besoins spécifiques ou extensions futures.

- `forest_protection_server.py` : Serveur Flask principal avec toutes les routes et la logique de détection
- `templates/base.html` : Template de base avec la structure commune à toutes les pages
- `templates/dashboard.html` : Page d'accueil avec mission et statistiques
- `templates/monitoring.html` : Page de surveillance vidéo avec détection d'incendies
- `templates/alerts.html` : Page pour les alertes citoyennes
- `static/css/styles.css` : Styles de l'interface
- `static/js/forest_protection.js` : Logique côté client pour la surveillance vidéo
- `static/img/forest-placeholder.jpg` : Image par défaut quand le flux n'est pas actif
- `static/img/forest-bg.jpg` : Image d'arrière-plan pour le tableau de bord
- `static/uploads/` : Dossier pour stocker les images d'alertes envoyées par les citoyens

## Personnalisation

- Modifiez les couleurs dans le fichier CSS pour adapter l'interface à votre charte graphique
- Ajustez les paramètres de détection YOLO dans la méthode `update` de la classe `VideoCamera`
- Personnalisez les alertes et les rapports dans le fichier JavaScript
