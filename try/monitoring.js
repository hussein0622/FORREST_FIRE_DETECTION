// Script pour la page de monitoring de GreenSentinel
// Gestion du flux vidéo et des contrôles de détection

let monitoringTime = 0;
let monitoringInterval = null;
let alertCount = 0;
let riskLevel = 0;

document.addEventListener('DOMContentLoaded', function() {
    // Éléments de l'interface
    const startButton = document.getElementById('start-stream');
    const stopButton = document.getElementById('stop-stream');
    const cameraSource = document.getElementById('camera-source');
    const videoFeed = document.getElementById('video-feed');
    const videoPlaceholder = document.getElementById('video-placeholder');
    const monitoringTimeDisplay = document.getElementById('monitoring-time');
    const alertCountDisplay = document.getElementById('alert-count');
    const riskLevelBar = document.getElementById('risk-level');
    const streamStatus = document.getElementById('stream-status');
    const lastUpdate = document.getElementById('last-update');

    // Démarrer automatiquement le flux vidéo
    function initVideoFeed() {
        if (videoFeed) {
            // Forcer le rechargement du flux
            videoFeed.src = '/video_feed?' + new Date().getTime();
            videoFeed.onload = function() {
                console.log('Flux vidéo chargé avec succès');
                if (videoPlaceholder) videoPlaceholder.style.display = 'none';
                videoFeed.style.display = 'block';
                startMonitoringTime();
                simulateAlerts();
                updateStreamStatus(true);
            };
            videoFeed.onerror = function() {
                console.error('Erreur de chargement du flux vidéo');
                if (videoPlaceholder) videoPlaceholder.style.display = 'block';
                videoFeed.style.display = 'none';
                updateStreamStatus(false);
            };
        }
    }

    // Mettre à jour le statut du flux
    function updateStreamStatus(isActive) {
        if (streamStatus) {
            if (isActive) {
                streamStatus.innerHTML = '<span class="badge bg-success">Actif <span class="record-dot"></span></span>';
            } else {
                streamStatus.innerHTML = '<span class="badge bg-danger">Erreur</span>';
            }
        }
    }

    // Vérifier si les éléments existent (page monitoring)
    if (startButton && stopButton) {
        // Démarrer automatiquement le flux
        initVideoFeed();
        
        // Événement pour redémarrer le flux
        startButton.addEventListener('click', function() {
            const source = cameraSource.value;
            startStream(source);
        });

        // Événement pour arrêter le flux
        stopButton.addEventListener('click', function() {
            stopStream();
        });
    }

    // Fonction pour démarrer le flux vidéo
    function startStream(source) {
        fetch('/api/start_stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ source: source }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' || data.status === 'already_running') {
                // Afficher le flux vidéo
                if (videoPlaceholder) videoPlaceholder.style.display = 'none';
                if (videoFeed) {
                    videoFeed.style.display = 'block';
                    // Force le rechargement du flux
                    videoFeed.src = '/video_feed?' + new Date().getTime();
                }
                
                // Mettre à jour l'interface
                if (startButton) startButton.disabled = true;
                if (stopButton) stopButton.disabled = false;
                if (streamStatus) {
                    streamStatus.innerHTML = '<span class="badge bg-success">Actif <span class="record-dot"></span></span>';
                }
                
                // Démarrer le compteur de temps
                startMonitoringTime();
                
                // Simuler des alertes périodiques
                simulateAlerts();
                
                showMessage('success', 'Flux vidéo démarré avec succès');
            } else {
                showMessage('danger', 'Erreur: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showMessage('danger', 'Erreur de connexion au serveur');
        });
    }

    // Fonction pour arrêter le flux vidéo
    function stopStream() {
        fetch('/api/stop_stream', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            // Afficher le placeholder
            if (videoPlaceholder) videoPlaceholder.style.display = 'block';
            if (videoFeed) videoFeed.style.display = 'none';
            
            // Mettre à jour l'interface
            if (startButton) startButton.disabled = false;
            if (stopButton) stopButton.disabled = true;
            if (streamStatus) {
                streamStatus.innerHTML = '<span class="badge bg-secondary">Inactif</span>';
            }
            
            // Arrêter le compteur de temps
            stopMonitoringTime();
            
            showMessage('info', 'Flux vidéo arrêté');
        })
        .catch(error => {
            console.error('Erreur:', error);
            showMessage('danger', 'Erreur de connexion au serveur');
        });
    }

    // Fonction pour afficher un message
    function showMessage(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Ajouter au conteneur de messages s'il existe
        const messagesContainer = document.querySelector('.container');
        if (messagesContainer) {
            messagesContainer.prepend(alertDiv);
            
            // Supprimer automatiquement après 5 secondes
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    }

    // Fonction pour démarrer le compteur de temps
    function startMonitoringTime() {
        // Réinitialiser si déjà en cours
        if (monitoringInterval) {
            clearInterval(monitoringInterval);
        }
        
        monitoringTime = 0;
        updateTimeDisplay();
        
        monitoringInterval = setInterval(() => {
            monitoringTime++;
            updateTimeDisplay();
            updateLastUpdate();
        }, 1000);
    }

    // Fonction pour arrêter le compteur de temps
    function stopMonitoringTime() {
        if (monitoringInterval) {
            clearInterval(monitoringInterval);
            monitoringInterval = null;
        }
    }

    // Fonction pour mettre à jour l'affichage du temps
    function updateTimeDisplay() {
        if (!monitoringTimeDisplay) return;
        
        const hours = Math.floor(monitoringTime / 3600);
        const minutes = Math.floor((monitoringTime % 3600) / 60);
        const seconds = monitoringTime % 60;
        
        monitoringTimeDisplay.textContent = 
            String(hours).padStart(2, '0') + ':' +
            String(minutes).padStart(2, '0') + ':' +
            String(seconds).padStart(2, '0');
    }

    // Fonction pour simuler des alertes périodiques
    function simulateAlerts() {
        // Simuler une alerte toutes les 20-60 secondes
        setTimeout(() => {
            if (monitoringInterval) {  // Vérifier si le monitoring est actif
                alertCount++;
                if (alertCountDisplay) alertCountDisplay.textContent = alertCount;
                
                // Augmenter le niveau de risque
                riskLevel = Math.min(100, riskLevel + Math.random() * 20);
                if (riskLevelBar) {
                    riskLevelBar.style.width = riskLevel + '%';
                    
                    // Changer la couleur en fonction du niveau
                    if (riskLevel < 30) {
                        riskLevelBar.className = 'progress-bar bg-success';
                    } else if (riskLevel < 70) {
                        riskLevelBar.className = 'progress-bar bg-warning';
                    } else {
                        riskLevelBar.className = 'progress-bar bg-danger';
                    }
                }
                
                // Afficher une notification
                showMessage('warning', 'Alerte: Détection potentielle d\'incendie');
                
                // Continuer la simulation
                simulateAlerts();
            }
        }, Math.random() * 40000 + 20000);  // Entre 20 et 60 secondes
    }

    // Fonction pour mettre à jour l'horodatage de dernière mise à jour
    function updateLastUpdate() {
        if (!lastUpdate) return;
        
        const now = new Date();
        lastUpdate.textContent = now.toLocaleTimeString();
    }
});
