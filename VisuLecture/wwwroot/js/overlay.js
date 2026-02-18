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

// Dessine un groupe de saccades avec courbe stylisée (arc pour recul, ligne droite pour avance)
window.drawSaccadeGroup = (points) => {
    const canvasInfo = window.initializeCanvas();
    if (!canvasInfo) return;
    
    const { ctx, scaleX, scaleY } = canvasInfo;
    
    if (points.length === 0) return;

    // Convertir les points avec le scaling
    const scaledPoints = points.map(p => ({
        x: p.x * scaleX,
        y: p.y * scaleY
    }));

    if (scaledPoints.length < 2) return;

    // Détecter la direction du mouvement (avance ou recul)
    const firstX = points[0].x;
    const lastX = points[points.length - 1].x;
    const isBackward = lastX < firstX; // Recul = déplacement vers la gauche

    const start = scaledPoints[0];
    const end = scaledPoints[scaledPoints.length - 1];

    // Calculer le point de contrôle pour l'arc
    const midX = (start.x + end.x) / 2;
    const midY = (start.y + end.y) / 2;
    
    // Décaler le point de contrôle pour créer un arc visible - TOUJOURS VERS LE HAUT
    const distance = Math.sqrt(Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2));
    const arcHeight = Math.max(distance * 0.35, 40);
    
    const controlX = midX;
    const controlY = midY - arcHeight; // Arc toujours vers le haut
    
    // TOUTES les saccades : arc de cercle en pointillés magenta
    ctx.strokeStyle = 'rgba(255, 100, 255, 0.8)';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    
    // Dessiner la courbe de Bézier quadratique en pointillés
    ctx.setLineDash([12, 6]);
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.quadraticCurveTo(controlX, controlY, end.x, end.y);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Dessiner une flèche à la fin pour indiquer la direction
    const arrowSize = 12;
    
    // Calculer l'angle de la tangente à la fin de la courbe
    // La dérivée de la courbe de Bézier quadratique à t=1 donne la direction
    const dx = 2 * (end.x - controlX);
    const dy = 2 * (end.y - controlY);
    const angle = Math.atan2(dy, dx);
    
    // Dessiner la flèche
    ctx.fillStyle = 'rgba(255, 100, 255, 0.9)';
    ctx.beginPath();
    ctx.moveTo(end.x, end.y);
    ctx.lineTo(
        end.x - arrowSize * Math.cos(angle - Math.PI / 6),
        end.y - arrowSize * Math.sin(angle - Math.PI / 6)
    );
    ctx.lineTo(
        end.x - arrowSize * Math.cos(angle + Math.PI / 6),
        end.y - arrowSize * Math.sin(angle + Math.PI / 6)
    );
    ctx.closePath();
    ctx.fill();
};

// Dessine un point unique
window.drawPoint = (x, y, color, radius = 4) => {
    const canvasInfo = window.initializeCanvas();
    if (!canvasInfo) return;
    
    const { ctx, scaleX, scaleY } = canvasInfo;

    // Ajuster les coordonnées
    const px = x * scaleX;
    const py = y * scaleY;

    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(px, py, radius, 0, Math.PI * 2);
    ctx.fill();
};

// Dessine une ligne épaissie avec des couleurs par segment
window.drawThickenedLineWithColors = (segments) => {
    const canvasInfo = window.initializeCanvas();
    if (!canvasInfo) return;
    
    const { ctx, scaleX, scaleY } = canvasInfo;

    segments.forEach(seg => {
        const x1 = seg.x1 * scaleX;
        const y1 = seg.y1 * scaleY;
        const x2 = seg.x2 * scaleX;
        const y2 = seg.y2 * scaleY;
        const width = seg.width * Math.min(scaleX, scaleY);
        const color = seg.color || 'red';

        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
    });
};

