// Script pour le système de protection des forêts

// Variables globales
let isStreaming = false;
let monitoringStartTime = null;
let monitoringTimer = null;
let alertCount = 0;

// Fonctions d'initialisation
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier l'état initial du streaming
    checkStreamStatus();
    
    // Initialiser les gestionnaires d'événements
    document.getElementById('start-stream').addEventListener('click', startStream);
    document.getElementById('stop-stream').addEventListener('click', stopStream);
});

// Vérifier l'état du flux vidéo
function checkStreamStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            updateUIStatus(data.is_streaming);
        })
        .catch(error => {
            console.error('Erreur lors de la vérification du statut:', error);
            updateUIStatus(false);
        });
}

// Démarrer le flux vidéo
function startStream() {
    const cameraSource = document.getElementById('camera-source').value.trim();
    
    fetch('/api/start_stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ source: cameraSource })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateUIStatus(true);
            
            // Afficher le flux vidéo
            document.getElementById('video-feed').src = '/video_feed?' + new Date().getTime();
            
            // Démarrer le moniteur de temps
            startMonitoringTimer();
        } else {
            showAlert('Erreur: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Erreur lors du démarrage du flux:', error);
        showAlert('Erreur de connexion au serveur', 'danger');
    });
}

// Arrêter le flux vidéo
function stopStream() {
    fetch('/api/stop_stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateUIStatus(false);
            
            // Arrêter le moniteur de temps
            stopMonitoringTimer();
            
            // Revenir à l'image par défaut
            document.getElementById('video-feed').src = '/static/img/forest-placeholder.jpg';
        } else {
            showAlert('Erreur: ' + data.message, 'warning');
        }
    })
    .catch(error => {
        console.error('Erreur lors de l\'arrêt du flux:', error);
        showAlert('Erreur de connexion au serveur', 'danger');
    });
}

// Mettre à jour l'interface utilisateur en fonction de l'état du streaming
function updateUIStatus(streaming) {
    isStreaming = streaming;
    
    // Mettre à jour l'indicateur de statut
    const statusBadge = document.getElementById('status-badge');
    statusBadge.textContent = streaming ? 'Connecté' : 'Déconnecté';
    statusBadge.className = streaming ? 'badge bg-success' : 'badge bg-danger';
    
    // Mettre à jour les boutons
    document.getElementById('start-stream').disabled = streaming;
    document.getElementById('stop-stream').disabled = !streaming;
    document.getElementById('camera-source').disabled = streaming;
    
    // Mettre à jour l'indicateur d'enregistrement
    const recordingIndicator = document.getElementById('recording-indicator');
    if (streaming) {
        recordingIndicator.classList.remove('d-none');
    } else {
        recordingIndicator.classList.add('d-none');
    }
    
    // Mettre à jour les statistiques de détection
    const detectionActive = document.getElementById('detection-active');
    if (streaming) {
        detectionActive.classList.remove('d-none');
    } else {
        detectionActive.classList.add('d-none');
    }
}

// Démarrer le compteur de temps de surveillance
function startMonitoringTimer() {
    monitoringStartTime = new Date();
    alertCount = 0;
    updateMonitoringTime();
    document.getElementById('alert-count').textContent = '0';
    
    // Mise à jour toutes les secondes
    monitoringTimer = setInterval(() => {
        updateMonitoringTime();
        
        // Simulation d'alertes aléatoires pour la démo
        if (Math.random() < 0.05 && isStreaming) {
            simulateAlert();
        }
    }, 1000);
}

// Arrêter le compteur de temps de surveillance
function stopMonitoringTimer() {
    if (monitoringTimer) {
        clearInterval(monitoringTimer);
        monitoringTimer = null;
    }
}

// Mettre à jour l'affichage du temps de surveillance
function updateMonitoringTime() {
    if (!monitoringStartTime) return;
    
    const now = new Date();
    const diff = now - monitoringStartTime;
    
    // Calculer heures, minutes, secondes
    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    
    // Formater le temps
    const timeString = 
        String(hours).padStart(2, '0') + ':' +
        String(minutes).padStart(2, '0') + ':' +
        String(seconds).padStart(2, '0');
    
    document.getElementById('monitoring-time').textContent = timeString;
}

// Simuler une alerte d'incendie (à des fins de démonstration)
function simulateAlert() {
    alertCount++;
    document.getElementById('alert-count').textContent = alertCount;
    
    // Calculer le niveau de risque (à des fins de démo)
    const riskLevel = Math.min(alertCount * 10, 100);
    const riskBar = document.getElementById('risk-level');
    
    riskBar.style.width = riskLevel + '%';
    riskBar.textContent = riskLevel + '%';
    
    // Changer la couleur en fonction du risque
    if (riskLevel < 30) {
        riskBar.className = 'progress-bar bg-success';
    } else if (riskLevel < 70) {
        riskBar.className = 'progress-bar bg-warning';
    } else {
        riskBar.className = 'progress-bar bg-danger';
    }
}

// Afficher une alerte à l'utilisateur
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Ajouter l'alerte au début du content
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-fermeture après 5 secondes
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}
