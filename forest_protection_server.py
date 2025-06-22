import os
import cv2
import time
import threading
import numpy as np
import datetime
import json
import base64
import uuid
from flask import Flask, render_template, Response, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import torch

# Importation de YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    print("Module YOLOv8 trouvé et chargé avec succès")
except ImportError:
    YOLO_AVAILABLE = False
    print("Module YOLOv8 non disponible. La détection d'incendies sera désactivée.")
    # Tentative d'installation automatique de YOLOv8
    try:
        import subprocess
        print("Tentative d'installation de YOLOv8...")
        subprocess.check_call(["pip", "install", "ultralytics"])
        from ultralytics import YOLO
        YOLO_AVAILABLE = True
        print("Module YOLOv8 installé et chargé avec succès")
    except Exception as e:
        print(f"Échec de l'installation automatique: {e}")

# Configuration
CAMERA_URL = "http://172.22.2.17:5000"  # URL du flux vidéo
MODEL_PATH = "last.pt"  # Chemin vers le modèle YOLOv8 entraîné pour la détection d'incendies
USE_DETECTION = YOLO_AVAILABLE  # Utiliser la détection si disponible

# Vérifier l'existence du modèle
if not os.path.exists(MODEL_PATH):
    print(f"Modèle {MODEL_PATH} non trouvé. Vérifiez le chemin du modèle.")
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Créer l'application Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "green_sentinel_secret_key")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# Variables globales
camera = None
is_streaming = False
output_frame = None
lock = threading.Lock()

class VideoCamera:
    def __init__(self, source=0):
        self.source = source
        self.video = None
        self.stopped = False
        self.model = None
        self.is_http_stream = str(source).startswith('http')
        self.frame = None
        self.lock = threading.Lock()
        
    def start(self):
        # Vérifier si c'est un flux HTTP ou une caméra locale
        if self.is_http_stream:
            print(f"Connexion au flux HTTP: {self.source}")
        else:
            # Essayer d'ouvrir la caméra locale
            try:
                self.video = cv2.VideoCapture(int(self.source) if self.source.isdigit() else self.source)
                if not self.video.isOpened():
                    raise ValueError(f"Impossible d'ouvrir la source vidéo: {self.source}")
                print(f"Connexion à la caméra réussie: {self.source}")
            except Exception as e:
                print(f"Erreur d'ouverture de la caméra: {e}")
                return None
        
        # Démarrer un thread pour lire les frames
        threading.Thread(target=self.update, daemon=True).start()
        return self
    
    def update(self):
        import requests
        import numpy as np
        
        # Variables pour le contrôle du FPS
        frame_count = 0
        detection_interval = 3  # Faire une détection toutes les 3 images (10 FPS pour la détection)
        last_detection = time.time()
        
        # Charger le modèle YOLO une seule fois
        model = None
        if YOLO_AVAILABLE:
            try:
                model = YOLO(MODEL_PATH)
                model.conf = 0.6  # Seuil de confiance optimal
                print("Modèle YOLOv8 chargé avec détection optimisée")
                
                # Optimiser pour la vitesse
                model.amp = True  # Mixed precision
                model.fuse()      # Fusionner les couches pour la vitesse
                
                # Désactiver les gradients pour l'inférence
                model.eval()
            except Exception as e:
                print(f"Erreur chargement YOLOv8: {e}")
                model = None

        if self.is_http_stream:
            # Pour les flux HTTP/MJPEG
            try:
                stream = requests.get(self.source, stream=True, timeout=5)  # Timeout plus court
                if stream.status_code != 200:
                    print(f"Erreur de connexion au flux HTTP: {stream.status_code}")
                    self.stopped = True
                    return
                
                bytes_data = bytes()
                last_detection = time.time()
                
                for chunk in stream.iter_content(chunk_size=8192):  # Taille de chunk augmentée
                    if self.stopped:
                        break
                    
                    bytes_data += chunk
                    a = bytes_data.find(b'\xff\xd8')
                    b = bytes_data.find(b'\xff\xd9')
                    
                    if a != -1 and b != -1:
                        jpg = bytes_data[a:b+2]
                        bytes_data = bytes_data[b+2:]
                        
                        # Décoder l'image JPEG
                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            # Redimensionner l'image pour accélérer le traitement
                            frame = cv2.resize(frame, (640, 480))  # Taille fixe pour la détection
                            
                            # Faire la détection à 10 FPS (toutes les 3 images)
                            frame_count += 1
                            if model is not None and frame_count % detection_interval == 0:
                                try:
                                    # Détection optimisée
                                    with torch.no_grad():  # Désactive le calcul des gradients
                                        results = model.track(
                                            source=frame,
                                            conf=0.6,
                                            verbose=False,
                                            persist=True,
                                            imgsz=640,  # Taille d'inférence optimale
                                            device='0' if torch.cuda.is_available() else 'cpu'
                                        )
                                    if results and len(results) > 0:
                                        frame = results[0].plot()
                                        last_detection = time.time()
                                except Exception as e:
                                    print(f"Erreur détection YOLO: {e}")
                            # Si pas de détection sur ce frame, utiliser le dernier frame traité
                            elif model is not None and 'last_processed_frame' in locals():
                                frame = last_processed_frame
                            
                            # Sauvegarder le dernier frame traité
                            last_processed_frame = frame.copy()
                            
                            # Mettre à jour le frame avec ou sans détection
                            with self.lock:
                                self.frame = frame.copy()
                                
            except Exception as e:
                print(f"Erreur avec le flux HTTP: {str(e)}")
                self.stopped = True
        else:
            # Pour les caméras locales et flux RTSP
            while not self.stopped:
                if self.video and self.video.isOpened():
                    success, frame = self.video.read()
                    if success:
                        if model is not None:
                            try:
                                results = model.predict(source=frame, conf=0.5, verbose=False)
                                annotated = results[0].plot()
                            except Exception as e:
                                print(f"Erreur détection YOLO: {e}")
                                annotated = frame
                            with self.lock:
                                self.frame = annotated.copy()
                        else:
                            with self.lock:
                                self.frame = frame.copy()
                    else:
                        print("Erreur de lecture du flux vidéo")
                        time.sleep(0.1)
                else:
                    time.sleep(0.1)
    
    def get_frame(self):
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()
    
    def stop(self):
        self.stopped = True
        if self.video and self.video.isOpened():
            self.video.release()
        print("Flux vidéo arrêté")
        
        if self.is_http_stream:
            # Pour les flux HTTP/MJPEG d'un autre serveur Flask
            try:
                stream = requests.get(self.source, stream=True, timeout=10)
                if stream.status_code != 200:
                    print(f"Erreur de connexion au flux HTTP: {stream.status_code}")
                    self.stopped = True
                    return
                    
                # Variables pour le parsing du stream MJPEG
                bytes_data = bytes()
                
                for chunk in stream.iter_content(chunk_size=1024):
                    if self.stopped:
                        break
                    
                    bytes_data += chunk
                    a = bytes_data.find(b'\xff\xd8')  # Début d'une image JPEG
                    b = bytes_data.find(b'\xff\xd9')  # Fin d'une image JPEG
                    
                    if a != -1 and b != -1:
                        jpg = bytes_data[a:b+2]
                        bytes_data = bytes_data[b+2:]
                        
                        # Décoder l'image JPEG
                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            # Traiter et mettre à jour l'affichage
                            processed_frame = process_frame(frame)
                            with lock:
                                output_frame = processed_frame.copy()
                        
                        # Pause courte pour contrôler la vitesse de traitement
                        time.sleep(0.01)
                        
            except Exception as e:
                print(f"Erreur avec le flux HTTP: {str(e)}")
                self.stopped = True
        else:
            # Pour les caméras locales et flux RTSP
            while not self.stopped:
                if self.video and self.video.isOpened():
                    success, frame = self.video.read()
                    if not success:
                        print("Erreur de lecture du frame")
                        # Tentative de reconnexion
                        self.video.release()
                        time.sleep(2)
                        self.video = cv2.VideoCapture(self.source)
                        continue
                    
                    # Traiter le frame et mettre à jour
                    processed_frame = process_frame(frame)
                    with lock:
                        output_frame = processed_frame.copy()
                else:
                    print("Flux vidéo fermé ou non disponible")
                    self.stopped = True
                    break
                
                # Limiter les FPS
                time.sleep(0.03)  # ~30 FPS
    
    def stop(self):
        self.stopped = True
        if self.video and self.video.isOpened():
            self.video.release()
            self.video = None
        print("Flux vidéo arrêté")

def generate_frames():
    global camera, lock
    print("Démarrage du générateur de frames optimisé")
    
    # Paramètres optimisés
    jpeg_quality = 60  # Bon équilibre qualité/performance
    target_fps = 30
    frame_time = 1.0 / target_fps
    last_frame_time = time.time()
    
    # Initialiser le codec vidéo
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    
    while True:
        try:
            if camera is None or camera.stopped:
                # Si pas de caméra, envoyer une image vide
                dummy_frame = np.zeros((target_height, target_width, 3), dtype=np.uint8)
                dummy_frame = cv2.putText(dummy_frame, 'En attente de flux vidéo...', (50, 240), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
                _, buffer = cv2.imencode('.jpg', dummy_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                yield (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + 
                      buffer.tobytes() + b'\r\n')
                time.sleep(1)
                continue
                
            frame = camera.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue
                
            # Encoder en JPEG avec optimisation
            success, buffer = cv2.imencode('.jpg', frame, [
                int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality,
                int(cv2.IMWRITE_JPEG_OPTIMIZE), 1
            ])
            
            if not success:
                continue
                
            # Contrôle de la vitesse pour maintenir le FPS cible
            current_time = time.time()
            elapsed = current_time - last_frame_time
            if elapsed < frame_time:
                time.sleep(max(0, frame_time - elapsed - 0.001))  # Réduire légèrement le sleep
            last_frame_time = time.time()
            
            # Envoyer le frame
            yield (b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + 
                  buffer.tobytes() + b'\r\n')
            
            # Pas besoin de sleep ici, le GIL fera le travail
            
        except Exception as e:
            print(f"Erreur dans generate_frames: {str(e)}")
            time.sleep(1)

# Définition de la mission et citation inspirante
MISSION = "Notre mission est de protéger les écosystèmes forestiers en utilisant des technologies avancées pour la détection précoce des incendies et la coordination rapide des interventions."

QUOTE = "La forêt précède les peuples, le désert les suit. — François-René de Chateaubriand"

# Initialisation des variables globales

@app.route('/')
def index():
    """Redirection vers le tableau de bord"""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Page de tableau de bord avec présentation du projet"""
    # Statistiques pour le tableau de bord
    now = datetime.datetime.now()
    today_alerts = [a for a in alerts_db.values() 
                   if (now - datetime.datetime.fromisoformat(a['timestamp'])).days < 1]
    
    stats = {
        'forests_monitored': 3,
        'alerts_today': len(today_alerts),
        'total_alerts': len(alerts_db),
        'detection_accuracy': 94.5
    }
    
    return render_template('dashboard.html', 
                         active_page='dashboard',
                         mission=MISSION,
                         quote=QUOTE,
                         stats=stats)

@app.route('/monitoring')
def monitoring():
    """Page de surveillance vidéo avec détection d'incendies"""
    global camera, is_streaming
    return render_template('monitoring.html', 
                         active_page='monitoring', 
                         yolo_available=YOLO_AVAILABLE)

@app.route('/video_feed')
def video_feed():
    """Flux vidéo pour la page web"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/start_stream', methods=['POST'])
def start_stream():
    """API pour démarrer le flux vidéo"""
    global camera, is_streaming, output_frame
    
    if is_streaming:
        return jsonify({"status": "already_running", "message": "Le streaming est déjà actif"})
    
    try:
        # Récupérer la source depuis le JSON ou utiliser la valeur par défaut
        camera_source = request.json.get('source', CAMERA_URL) if request.json else CAMERA_URL
        print(f"Démarrage du flux vidéo depuis {camera_source}")
        
        # Initialiser la caméra
        camera = VideoCamera(camera_source)
        result = camera.start()
        
        if result is None:
            return jsonify({"status": "error", "message": "Impossible de démarrer le flux vidéo"})
        
        is_streaming = True
        print("Flux vidéo démarré avec succès")
        
        # Initialiser le frame de sortie avec un message
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        dummy_frame = cv2.putText(dummy_frame, 'Connexion...', (220, 240), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        with lock:
            output_frame = dummy_frame
        
        return jsonify({"status": "success", "message": "Flux vidéo démarré avec succès"})
    except Exception as e:
        print(f"Erreur lors du démarrage du flux: {str(e)}")
        return jsonify({"status": "error", "message": f"Erreur: {str(e)}"})

@app.route('/api/stop_stream', methods=['POST'])
def stop_stream():
    """API pour arrêter le flux vidéo"""
    global camera, is_streaming
    
    if not is_streaming:
        return jsonify({"status": "not_running", "message": "Le streaming n'est pas actif"})
    
    try:
        if camera:
            camera.stop()
            camera = None
        is_streaming = False
        return jsonify({"status": "success", "message": "Flux vidéo arrêté avec succès"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Erreur: {str(e)}"})

@app.route('/api/status')
def status():
    """API pour vérifier l'état du flux vidéo"""
    return jsonify({"is_streaming": is_streaming})

@app.route('/alerts', endpoint='alerts')
def submit_alert():
    """Page pour soumettre une nouvelle alerte (version publique)"""
    return render_template('submit_alert.html', active_page='alerts')

# Fonctions utilitaires pour les alertes citoyennes
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Dictionnaire pour stocker les alertes (à remplacer par une base de données en production)
alerts_db = {}

@app.route('/admin/alerts')
def manage_alerts():
    """Page d'administration pour gérer les alertes"""
    # Vérifier l'authentification ici (à implémenter)
    return render_template('admin/alerts.html', active_page='admin_alerts')

# API pour gérer les alertes
@app.route('/api/alerts', methods=['GET', 'POST'])
def api_alerts():
    if request.method == 'GET':
        # Récupérer les paramètres de filtrage
        status_filter = request.args.get('status', 'all')
        search_term = request.args.get('search', '').lower()
        
        # Filtrer les alertes
        filtered_alerts = []
        for alert_id, alert in alerts_db.items():
            # Filtrer par statut
            if status_filter != 'all' and alert.get('status') != status_filter:
                continue
                
            # Filtrer par terme de recherche
            if search_term:
                search_in = f"{alert.get('location', '')} {alert.get('description', '')}".lower()
                if search_term not in search_in:
                    continue
            
            filtered_alerts.append(alert)
        
        # Trier par date (les plus récentes en premier)
        filtered_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify(filtered_alerts)
    
    elif request.method == 'POST':
        # Créer une nouvelle alerte
        try:
            data = request.form
            files = request.files
            
            # Générer un ID unique
            alert_id = str(uuid.uuid4())
            
            # Gérer le téléchargement de l'image
            image_path = None
            if 'image' in files and files['image'].filename != '':
                image = files['image']
                if image and allowed_file(image.filename):
                    filename = secure_filename(f"{alert_id}_{image.filename}")
                    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'alerts'), exist_ok=True)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'alerts', filename)
                    image.save(image_path)
                    image_path = f"/static/uploads/alerts/{filename}"
            
            # Créer l'alerte
            alert = {
                'id': alert_id,
                'name': data.get('name', 'Anonyme'),
                'location': data.get('location', 'Localisation inconnue'),
                'description': data.get('description', 'Aucune description fournie'),
                'severity': data.get('severity', 'medium'),
                'status': 'new',  # Nouvelle alerte
                'image': image_path,
                'timestamp': datetime.datetime.now().isoformat(),
                'coordinates': None  # À implémenter avec la géolocalisation
            }
            
            # Sauvegarder l'alerte
            alerts_db[alert_id] = alert
            
            # Ici, vous pourriez ajouter une notification en temps réel
            
            return jsonify({'status': 'success', 'message': 'Alerte enregistrée avec succès', 'alert_id': alert_id})
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/alerts/<alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """Mettre à jour le statut d'une alerte"""
    if alert_id not in alerts_db:
        return jsonify({'status': 'error', 'message': 'Alerte non trouvée'}), 404
    
    try:
        data = request.get_json()
        if 'status' in data and data['status'] in ['new', 'in_progress', 'resolved']:
            alerts_db[alert_id]['status'] = data['status']
            return jsonify({'status': 'success', 'message': 'Statut mis à jour'})
        else:
            return jsonify({'status': 'error', 'message': 'Statut invalide'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Assurez-vous que les dossiers nécessaires existent
def create_dirs():
    os.makedirs('static', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/img', exist_ok=True)
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('templates', exist_ok=True)

if __name__ == '__main__':
    create_dirs()
    # Utiliser l'adresse IP spécifiée
    app.run(host='0.0.0.0', port=5000, debug=True)
