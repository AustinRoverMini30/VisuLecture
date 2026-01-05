let mediaRecorder;
let chunks = [];
let stream;
let indexRecording = 0;
let calibrationIndex = "";
let recordedBlob = [];
let recordRead = null;

async function startRecording(index, calibrationId) {
    if (calibrationId != null) {
        document.cookie = `calibrationId=${calibrationId}; path=/; max-age=3600; SameSite=Strict`;
    }
    indexRecording = index;
    calibrationIndex = calibrationId;
    stream = await navigator.mediaDevices.getUserMedia({ video: {
            width: { ideal: 1920 },
            height: { ideal: 1080 },
            frameRate: { ideal: 60 },
            aspectRatio: { ideal: 16/9 }

        }, audio: false });
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