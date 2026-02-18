let mediaRecorder;
let chunks = [];
let stream;
let indexRecording = 0;
let calibrationIndex = "";
let recordedBlob = [];
let recordRead = null;
let selectedCamera = null; // Stocker la caméra sélectionnée

// Variables pour la gestion de la durée
let recordingTimer = null;
let onDurationReached = null;

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
        frameRate: { ideal: 30 }, // Réduire à 30 fps pour plus de stabilité
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

    // Sélectionner le meilleur codec disponible
    let options = { mimeType: 'video/webm;codecs=vp8' };
    
    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        console.warn('vp8 not supported, trying vp9');
        options = { mimeType: 'video/webm;codecs=vp9' };
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            console.warn('vp9 not supported, using default');
            options = { mimeType: 'video/webm' };
        }
    }
    
    console.log('Using mimeType:', options.mimeType);
    
    mediaRecorder = new MediaRecorder(stream, options);
    chunks = [];

    mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) {
            console.log(`Data chunk received: ${e.data.size} bytes`);
            chunks.push(e.data);
        }
    };
    
    mediaRecorder.onerror = e => {
        console.error("MediaRecorder error:", e);
    };

    // Utiliser un timeslice de 100ms pour créer des segments plus petits et mieux formés
    mediaRecorder.start(100);
    console.log("Recording started with timeslice of 100ms");
}

// Fonction pour démarrer l'enregistrement avec limite de durée (en secondes)
async function startRecordingWithDuration(index, calibrationId, durationSeconds, dotNetHelper) {
    if (calibrationId != null) {
        document.cookie = `calibrationId=${calibrationId}; path=/; max-age=3600; SameSite=Strict`;
    }
    indexRecording = index;
    calibrationIndex = calibrationId;
    onDurationReached = dotNetHelper;
    
    // Arrêter le flux de test si actif
    stopCameraTest();
    
    // Utiliser la caméra sélectionnée si disponible
    const videoConstraints = {
        width: { ideal: 1920 },
        height: { ideal: 1080 },
        frameRate: { ideal: 30 },
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

    // Sélectionner le meilleur codec disponible
    let options = { mimeType: 'video/webm;codecs=vp8' };
    
    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        console.warn('vp8 not supported, trying vp9');
        options = { mimeType: 'video/webm;codecs=vp9' };
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            console.warn('vp9 not supported, using default');
            options = { mimeType: 'video/webm' };
        }
    }
    
    console.log('Using mimeType:', options.mimeType);
    
    mediaRecorder = new MediaRecorder(stream, options);
    chunks = [];

    mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) {
            chunks.push(e.data);
            console.log(`Data chunk received: ${e.data.size} bytes`);
        }
    };
    
    mediaRecorder.onerror = e => {
        console.error("MediaRecorder error:", e);
    };

    mediaRecorder.start(100); // Timeslice de 100ms
    console.log(`Recording started with duration: ${durationSeconds} seconds`);
    
    // Démarrer le timer pour arrêter après la durée spécifiée
    recordingTimer = setTimeout(() => {
        console.log(`Duration reached: ${durationSeconds} seconds`);
        stopCurrentRecordingByDuration();
    }, durationSeconds * 1000);
}

// Fonction pour arrêter l'enregistrement actuel et sauvegarder (déclenchée par la durée)
function stopCurrentRecordingByDuration() {
    // Nettoyer le timer
    if (recordingTimer) {
        clearTimeout(recordingTimer);
        recordingTimer = null;
    }
    
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        return;
    }

    mediaRecorder.onstop = () => {
        // Créer un Blob bien formé avec le bon type MIME
        const mimeType = mediaRecorder.mimeType || "video/webm";
        const blob = new Blob(chunks, { type: mimeType });
        
        // Sauvegarder la vidéo enregistrée
        if (recordedBlob.length <= indexRecording) {
            recordedBlob.push(blob);
        } else {
            recordedBlob[indexRecording] = blob;
        }

        console.log(`Video ${indexRecording} saved. Blob size: ${blob.size} bytes`);

        // Incrémenter l'index pour la prochaine vidéo
        indexRecording++;
        
        // Réinitialiser les chunks pour la prochaine vidéo
        chunks = [];
        
        // Appeler le callback C# pour passer au point suivant
        if (onDurationReached) {
            onDurationReached.invokeMethodAsync('OnDurationReached');
        }
    };

    mediaRecorder.stop();
}

// Fonction pour redémarrer l'enregistrement pour le point suivant
async function startNextPointRecordingByDuration(durationSeconds, dotNetHelper) {
    onDurationReached = dotNetHelper;
    chunks = [];
    
    // Redémarrer l'enregistrement avec le même MediaRecorder
    mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) {
            chunks.push(e.data);
            console.log(`Data chunk received: ${e.data.size} bytes`);
        }
    };
    
    mediaRecorder.start(100);
    console.log(`Recording restarted for video ${indexRecording} with duration: ${durationSeconds} seconds`);
    
    // Démarrer le timer pour arrêter après la durée spécifiée
    recordingTimer = setTimeout(() => {
        console.log(`Duration reached: ${durationSeconds} seconds`);
        stopCurrentRecordingByDuration();
    }, durationSeconds * 1000);
}

// Fonction pour arrêter complètement la calibration
function stopCalibrationRecordingByDuration() {
    return new Promise(resolve => {
        // Nettoyer le timer si actif
        if (recordingTimer) {
            clearTimeout(recordingTimer);
            recordingTimer = null;
        }
        
        if (!mediaRecorder || mediaRecorder.state === 'inactive') {
            // Arrêter la caméra
            if (stream) {
                stream.getTracks().forEach(t => t.stop());
            }
            resolve();
            return;
        }

        mediaRecorder.onstop = () => {
            // Créer un Blob pour la dernière vidéo
            const mimeType = mediaRecorder.mimeType || "video/webm";
            const blob = new Blob(chunks, { type: mimeType });
            
            if (recordedBlob.length <= indexRecording) {
                recordedBlob.push(blob);
            } else {
                recordedBlob[indexRecording] = blob;
            }

            console.log(`Final video ${indexRecording} saved. Blob size: ${blob.size} bytes`);
            console.log(`Total videos recorded: ${recordedBlob.length}`);

            // Arrêter la caméra
            if (stream) {
                stream.getTracks().forEach(t => t.stop());
            }
            
            // Réinitialiser
            chunks = [];
            
            resolve();
        };

        mediaRecorder.stop();
    });
}

// Fonction pour démarrer l'enregistrement avec limite de frames
async function startRecordingWithFrameLimit(index, calibrationId, maxFrames, dotNetHelper) {
    if (calibrationId != null) {
        document.cookie = `calibrationId=${calibrationId}; path=/; max-age=3600; SameSite=Strict`;
    }
    indexRecording = index;
    calibrationIndex = calibrationId;
    frameCount = 0;
    frameLimit = maxFrames;
    onFrameLimitReached = dotNetHelper;
    
    // Arrêter le flux de test si actif
    stopCameraTest();
    
    // Utiliser la caméra sélectionnée si disponible
    const videoConstraints = {
        width: { ideal: 1920 },
        height: { ideal: 1080 },
        frameRate: { exact: fps },
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

    // Sélectionner le meilleur codec disponible
    let options = { mimeType: 'video/webm;codecs=vp8' };
    
    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        console.warn('vp8 not supported, trying vp9');
        options = { mimeType: 'video/webm;codecs=vp9' };
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            console.warn('vp9 not supported, using default');
            options = { mimeType: 'video/webm' };
        }
    }
    
    console.log('Using mimeType:', options.mimeType);
    
    mediaRecorder = new MediaRecorder(stream, options);
    chunks = [];

    let lastTime = performance.now();

    mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) {
            chunks.push(e.data);
            
            // Estimer le nombre de frames dans ce chunk
            const currentTime = performance.now();
            const elapsed = (currentTime - lastTime) / 1000; // en secondes
            const estimatedFrames = Math.round(elapsed * fps);
            lastTime = currentTime;
            
            frameCount += Math.max(1, estimatedFrames);
            
            console.log(`Frame count: ${frameCount}/${frameLimit}, chunk size: ${e.data.size} bytes`);
            
            // Si on atteint la limite de frames
            if (frameCount >= frameLimit) {
                console.log(`Frame limit reached: ${frameCount} frames`);
                stopCurrentRecording();
            }
        }
    };
    
    mediaRecorder.onerror = e => {
        console.error("MediaRecorder error:", e);
    };

    mediaRecorder.start(33); // ~30 fps = 33ms par timeslice
    console.log(`Recording started with frame limit: ${frameLimit} frames at ${fps} fps`);
}

// Fonction pour arrêter l'enregistrement actuel et sauvegarder
function stopCurrentRecording() {
    return new Promise(resolve => {
        if (!mediaRecorder || mediaRecorder.state === 'inactive') {
            resolve();
            return;
        }

        mediaRecorder.onstop = () => {
            // Créer un Blob bien formé avec le bon type MIME
            const mimeType = mediaRecorder.mimeType || "video/webm";
            const blob = new Blob(chunks, { type: mimeType });
            
            // Sauvegarder la vidéo enregistrée
            if (recordedBlob.length <= indexRecording) {
                recordedBlob.push(blob);
            } else {
                recordedBlob[indexRecording] = blob;
            }

            console.log(`Video ${indexRecording} saved. Frames: ${frameCount}, Blob size: ${blob.size} bytes`);

            // Incrémenter l'index pour la prochaine vidéo
            indexRecording++;
            
            // Réinitialiser les chunks pour la prochaine vidéo
            chunks = [];
            frameCount = 0;
            
            // Appeler le callback C# pour passer au point suivant
            if (onFrameLimitReached) {
                onFrameLimitReached.invokeMethodAsync('OnFrameLimitReached');
            }

            resolve();
        };

        mediaRecorder.stop();
    });
}

// Fonction pour redémarrer l'enregistrement pour le point suivant
async function startNextPointRecording(maxFrames, dotNetHelper) {
    frameCount = 0;
    frameLimit = maxFrames;
    onFrameLimitReached = dotNetHelper;
    chunks = [];
    
    // Redémarrer l'enregistrement avec le même MediaRecorder
    let lastTime = performance.now();
    
    mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) {
            chunks.push(e.data);
            
            // Estimer le nombre de frames dans ce chunk
            const currentTime = performance.now();
            const elapsed = (currentTime - lastTime) / 1000;
            const estimatedFrames = Math.round(elapsed * fps);
            lastTime = currentTime;
            
            frameCount += Math.max(1, estimatedFrames);
            
            console.log(`Frame count: ${frameCount}/${frameLimit}, chunk size: ${e.data.size} bytes`);
            
            // Si on atteint la limite de frames
            if (frameCount >= frameLimit) {
                console.log(`Frame limit reached: ${frameCount} frames`);
                stopCurrentRecording();
            }
        }
    };
    
    mediaRecorder.start(33);
    console.log(`Recording restarted for video ${indexRecording} with frame limit: ${frameLimit} frames`);
}

// Fonction pour arrêter complètement la calibration
function stopCalibrationRecording() {
    return new Promise(resolve => {
        if (!mediaRecorder || mediaRecorder.state === 'inactive') {
            // Arrêter la caméra
            if (stream) {
                stream.getTracks().forEach(t => t.stop());
            }
            resolve();
            return;
        }

        mediaRecorder.onstop = () => {
            // Créer un Blob pour la dernière vidéo
            const mimeType = mediaRecorder.mimeType || "video/webm";
            const blob = new Blob(chunks, { type: mimeType });
            
            if (recordedBlob.length <= indexRecording) {
                recordedBlob.push(blob);
            } else {
                recordedBlob[indexRecording] = blob;
            }

            console.log(`Final video ${indexRecording} saved. Frames: ${frameCount}, Blob size: ${blob.size} bytes`);
            console.log(`Total videos recorded: ${recordedBlob.length}`);

            // Arrêter la caméra
            if (stream) {
                stream.getTracks().forEach(t => t.stop());
            }
            
            // Réinitialiser
            chunks = [];
            frameCount = 0;
            
            resolve();
        };

        mediaRecorder.stop();
    });
}

// Fonction pour définir la caméra sélectionnée
function setSelectedCamera(deviceId) {
    selectedCamera = deviceId;
}

function stopRecording() {
    return new Promise(resolve => {
        mediaRecorder.onstop = () => {
            // Créer un Blob bien formé avec le bon type MIME
            const mimeType = mediaRecorder.mimeType || "video/webm";
            const blob = new Blob(chunks, { type: mimeType });
            
            // Sauvegarder la vidéo enregistrée
            if (recordedBlob.length <= indexRecording) {
                recordedBlob.push(blob);
            } else {
                recordedBlob[indexRecording] = blob;
            }

            console.log(`Recording stopped. Blob size: ${blob.size} bytes, type: ${mimeType}`);

            // Arrêter la caméra
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
    
    // Réinitialiser après upload
    recordedBlob = [];
    chunks = [];
    indexRecording = 0;
}


function switchRecording2() {
    return new Promise(resolve => {
        mediaRecorder.onstop = () => {
            // Créer un Blob bien formé avec le bon type MIME
            const mimeType = mediaRecorder.mimeType || "video/webm";
            recordRead = new Blob(chunks, { type: mimeType });

            console.log(`Recording stopped. Blob size: ${recordRead.size} bytes, type: ${mimeType}`);

            chunks = [];

            // Redémarrer avec le même timeslice
            mediaRecorder.start(100);
            console.log("Recording restarted with timeslice of 100ms");

            resolve();
        };

        mediaRecorder.stop();
    });
}

function stopRecording2Final() {
    return new Promise(resolve => {
        mediaRecorder.onstop = () => {
            // Créer un Blob bien formé avec le bon type MIME
            const mimeType = mediaRecorder.mimeType || "video/webm";
            recordRead = new Blob(chunks, { type: mimeType });

            console.log(`Final recording stopped. Blob size: ${recordRead.size} bytes, type: ${mimeType}`);

            chunks = [];

            // Arrêter la caméra
            if (stream) {
                stream.getTracks().forEach(t => t.stop());
                console.log("Camera stream stopped");
            }

            resolve();
        };

        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        } else {
            console.warn("MediaRecorder already stopped");
            resolve();
        }
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

