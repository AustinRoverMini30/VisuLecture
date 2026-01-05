let mediaRecorder;
let chunks = [];
let stream;
let indexRecording = 0;
let calibrationIndex = "";
let recordedBlob = [];
let recordRead = null;
let selectedCamera = null; // Stocker la caméra sélectionnée

async function startRecording(index, calibrationId) {
    if (calibrationId != null) {
        document.cookie = `calibrationId=${calibrationId}; path=/; max-age=3600; SameSite=Strict`;
    }
    indexRecording = index;
    calibrationIndex = calibrationId;
    
    // Arrêter le flux de test si actif
    stopCameraTest();
    
    // Utiliser la caméra sélectionnée si disponible
    const videoConstraints = {
        width: { ideal: 1920 },
        height: { ideal: 1080 },
        frameRate: { ideal: 60 },
        aspectRatio: { ideal: 16/9 }
    };
    
    if (selectedCamera) {
        videoConstraints.deviceId = { exact: selectedCamera };
    }
    
    stream = await navigator.mediaDevices.getUserMedia({ 
        video: videoConstraints, 
        audio: false 
    });
    
    const preview = document.getElementById("preview");
    preview.srcObject = stream;

    mediaRecorder = new MediaRecorder(stream, { mimeType: "video/webm" });
    chunks = [];

    mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) chunks.push(e.data);
    };

    mediaRecorder.start();
    console.log("Recording started");
}

// Fonction pour définir la caméra sélectionnée
function setSelectedCamera(deviceId) {
    selectedCamera = deviceId;
}

function stopRecording() {
    return new Promise(resolve => {
        mediaRecorder.onstop = () => {

            // stop cam
            stream.getTracks().forEach(t => t.stop());

            resolve();
        };

        mediaRecorder.stop();
    });
}

function switchRecording() {
    return new Promise(resolve => {
        mediaRecorder.onstop = () => {

            if (recordedBlob.length <= indexRecording) {
                recordedBlob.push(new Blob(chunks, { type: "video/webm" }));
            }else{
                recordedBlob[indexRecording] = new Blob(chunks, { type: "video/webm" });
            }

            console.log("Recording stopped. Blob size:", recordedBlob[indexRecording].size);

            indexRecording++;

            chunks = [];

            console.log("Recording started");

            resolve();
        };

        mediaRecorder.stop();
        mediaRecorder.start();
    });
}

async function uploadVideo(readingId) {

    for (let i = 0; i < recordedBlob.length; i++) {
        const form = new FormData();
        form.append("file", recordedBlob[i], "video" + i + ".webm");
        form.append("client-id", readingId)
        const response = await fetch("/api/video/upload", {
            method: "POST",
            body: form
        });

        if (!response.ok) {
            return "Erreur";
        }
    }
}


function switchRecording2() {
    return new Promise(resolve => {
        mediaRecorder.onstop = () => {

            recordRead = new Blob(chunks, { type: "video/webm" });

            console.log("Recording stopped. Blob size:", recordRead.size);

            chunks = [];

            console.log("Recording started");

            resolve();
        };

        mediaRecorder.stop();
        mediaRecorder.start();
    });
}

async function uploadVideo2(readingId) {
    const form = new FormData();
    form.append("file", recordRead, "reading.webm");
    form.append("client-id", readingId)
    const response = await fetch("/api/video/upload", {
        method: "POST",
        body: form
    });

    if (!response.ok) {
        alert("Erreur upload !");
    }
}

async function getCalibrationIdFromCookie() {
    const name = "calibrationId=";
    const decoded = decodeURIComponent(document.cookie);
    const parts = decoded.split("; ");
    for (const part of parts) {
        if (part.startsWith(name)) {
            return part.substring(name.length);
        }
    }
    return null;
}

// Variables pour le test de caméra
let testStream = null;

// Fonction pour obtenir la liste des caméras disponibles
async function getAvailableCameras() {
    try {
        // Demander l'accès aux caméras pour pouvoir lister les périphériques
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        stream.getTracks().forEach(track => track.stop()); // Arrêter immédiatement

        const devices = await navigator.mediaDevices.enumerateDevices();
        const cameras = devices
            .filter(device => device.kind === 'videoinput')
            .map(device => ({
                deviceId: device.deviceId,
                label: device.label || `Caméra ${device.deviceId.substring(0, 8)}`
            }));
        
        return cameras;
    } catch (error) {
        console.error("Erreur lors de l'énumération des caméras:", error);
        return [];
    }
}

// Fonction pour tester une caméra spécifique
async function testCamera(deviceId) {
    try {
        // Arrêter le flux précédent s'il existe
        if (testStream) {
            testStream.getTracks().forEach(track => track.stop());
            testStream = null;
        }

        // Attendre un peu pour que le flux précédent se libère complètement
        await new Promise(resolve => setTimeout(resolve, 100));

        // Attendre que l'élément vidéo existe dans le DOM
        let preview = document.getElementById("camera-test-preview");
        let attempts = 0;
        while (!preview && attempts < 20) {
            await new Promise(resolve => setTimeout(resolve, 50));
            preview = document.getElementById("camera-test-preview");
            attempts++;
        }
        
        if (!preview) {
            console.error("Élément vidéo 'camera-test-preview' non trouvé dans le DOM");
            return false;
        }

        // Démarrer un nouveau flux avec la caméra sélectionnée
        testStream = await navigator.mediaDevices.getUserMedia({
            video: {
                deviceId: deviceId ? { exact: deviceId } : undefined,
                width: { ideal: 1920 },
                height: { ideal: 1080 },
                frameRate: { ideal: 30 }
            }
        });

        // Forcer le rechargement du flux
        preview.srcObject = null;
        await new Promise(resolve => setTimeout(resolve, 50));
        preview.srcObject = testStream;
        
        // S'assurer que la vidéo démarre
        try {
            await preview.play();
        } catch (err) {
            console.log("Erreur play (peut être ignorée si autoplay fonctionne):", err);
        }

        console.log("Caméra de test démarrée avec succès");
        return true;
    } catch (error) {
        console.error("Erreur lors du test de la caméra:", error);
        return false;
    }
}

// Fonction pour arrêter le test de caméra
function stopCameraTest() {
    if (testStream) {
        testStream.getTracks().forEach(track => track.stop());
        testStream = null;
    }
    
    const preview = document.getElementById("camera-test-preview");
    if (preview) {
        preview.srcObject = null;
    }
}

