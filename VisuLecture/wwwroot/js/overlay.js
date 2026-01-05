window.drawFollowLine = (points, lineColor = "red", pointColor = "blue") => {

    const img = document.getElementById("backgroundImage");
    const canvas = document.getElementById("overlayCanvas");
    const ctx = canvas.getContext("2d");

    // Adapter le canvas à la taille affichée de l'image (seulement si nécessaire)
    if (canvas.width !== img.clientWidth || canvas.height !== img.clientHeight) {
        canvas.width = img.clientWidth;
        canvas.height = img.clientHeight;
    }

    // Ratio d'échelle (image affichée → image réelle)
    const scaleX = img.clientWidth / img.naturalWidth;
    const scaleY = img.clientHeight / img.naturalHeight;

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
    const img = document.getElementById("backgroundImage");
    const canvas = document.getElementById("overlayCanvas");
    const ctx = canvas.getContext("2d");

    // Ratio d'échelle (image affichée → image réelle)
    const scaleX = img.clientWidth / img.naturalWidth;
    const scaleY = img.clientHeight / img.naturalHeight;

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
    const img = document.getElementById("backgroundImage");
    const canvas = document.getElementById("overlayCanvas");
    const ctx = canvas.getContext("2d");

    // Ratio d'échelle (image affichée → image réelle)
    const scaleX = img.clientWidth / img.naturalWidth;
    const scaleY = img.clientHeight / img.naturalHeight;

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

