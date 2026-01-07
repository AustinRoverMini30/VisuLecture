// Fonction utilitaire pour initialiser le canvas et obtenir le contexte avec scaling
window.initializeCanvas = () => {
    const img = document.getElementById("backgroundImage");
    const canvas = document.getElementById("overlayCanvas");
    
    if (!img || !canvas) {
        console.error("Image ou canvas introuvable");
        return null;
    }
    
    const ctx = canvas.getContext("2d");
    
    // Adapter le canvas à la taille affichée de l'image
    if (canvas.width !== img.clientWidth || canvas.height !== img.clientHeight) {
        canvas.width = img.clientWidth;
        canvas.height = img.clientHeight;
    }
    
    // Calculer les ratios d'échelle
    const scaleX = img.clientWidth / img.naturalWidth;
    const scaleY = img.clientHeight / img.naturalHeight;
    
    return { ctx, img, canvas, scaleX, scaleY };
};

window.drawFollowLine = (points, lineColor = "red", pointColor = "blue") => {
    const canvasInfo = window.initializeCanvas();
    if (!canvasInfo) return;
    
    const { ctx, scaleX, scaleY } = canvasInfo;

    // --- Tracé de la ligne suivant les points ---
    ctx.lineWidth = 3;
    ctx.strokeStyle = lineColor;
    ctx.beginPath();

    points.forEach((p, index) => {
        const x = p.x * scaleX;
        const y = p.y * scaleY;

        if (index === 0)
            ctx.moveTo(x, y);
        else
            ctx.lineTo(x, y);
    });

    ctx.stroke();

    // --- Ajout des petits points ---
    ctx.fillStyle = pointColor;

    points.forEach((p) => {
        const x = p.x * scaleX;
        const y = p.y * scaleY;

        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
    });
};

// Efface complètement le canvas
window.clearOverlay = () => {
    const canvas = document.getElementById("overlayCanvas");
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
};

// Dessine un cercle de densité
window.drawDensityCircle = (centerX, centerY, radius, color) => {
    const canvasInfo = window.initializeCanvas();
    if (!canvasInfo) return;
    
    const { ctx, scaleX, scaleY } = canvasInfo;

    // Ajuster les coordonnées
    const x = centerX * scaleX;
    const y = centerY * scaleY;
    const r = radius * Math.min(scaleX, scaleY);

    // Dessiner le cercle rempli
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
    
    // Ajouter un contour semi-transparent pour mieux voir les cercles
    ctx.strokeStyle = color.replace(/[\d.]+\)$/, '0.9)'); // Augmenter l'opacité du contour
    ctx.lineWidth = 2;
    ctx.stroke();
};

// Dessine une boîte autour d'un mot
window.drawWordBox = (x, y, width, height, borderColor) => {
    const canvasInfo = window.initializeCanvas();
    if (!canvasInfo) return;
    
    const { ctx, scaleX, scaleY } = canvasInfo;

    // Ajuster les coordonnées et dimensions
    const scaledX = x * scaleX;
    const scaledY = y * scaleY;
    const scaledWidth = width * scaleX;
    const scaledHeight = height * scaleY;

    // Dessiner le rectangle
    ctx.strokeStyle = borderColor;
    ctx.lineWidth = 2;
    ctx.strokeRect(scaledX, scaledY, scaledWidth, scaledHeight);
};

// Dessine des segments avec épaisseur variable selon la distance entre les points
window.drawThickenedLine = (segments, lineColor) => {
    const canvasInfo = window.initializeCanvas();
    if (!canvasInfo) return;
    
    const { ctx, scaleX, scaleY } = canvasInfo;

    ctx.strokeStyle = lineColor;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // Dessiner chaque segment avec son épaisseur spécifique
    segments.forEach((segment) => {
        const x1 = segment.x1 * scaleX;
        const y1 = segment.y1 * scaleY;
        const x2 = segment.x2 * scaleX;
        const y2 = segment.y2 * scaleY;
        
        ctx.lineWidth = segment.width;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
    });
};

// Dessine un point individuel
window.drawPoint = (x, y, color, radius) => {
    const canvasInfo = window.initializeCanvas();
    if (!canvasInfo) return;
    
    const { ctx, scaleX, scaleY } = canvasInfo;

    const scaledX = x * scaleX;
    const scaledY = y * scaleY;

    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(scaledX, scaledY, radius, 0, Math.PI * 2);
    ctx.fill();
};

