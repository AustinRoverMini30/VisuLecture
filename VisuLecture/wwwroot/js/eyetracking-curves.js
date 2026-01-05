// Simulation de courbes d'eye-tracking réalistes
class EyeTrackingCurve {
    constructor(svgElement, pathElement, color, delay) {
        this.svg = svgElement;
        this.path = pathElement;
        this.color = color;
        this.delay = delay;
        this.points = [];
        this.currentIndex = 0;
        this.isDrawing = false;
        this.pathString = '';
    }

    // Génère une trajectoire d'eye-tracking réaliste
    generateRealisticPath() {
        this.points = [];
        const viewportWidth = 1920;
        const viewportHeight = 100;
        
        let x = -100;
        let y = Math.random() * 40 + 30; // Entre 30 et 70
        
        // Point de départ
        this.points.push({ x, y });
        
        // Génère des points avec mouvement saccadé typique de l'eye-tracking
        while (x < viewportWidth + 200) {
            // Saccade (mouvement rapide)
            const saccadeLength = Math.random() * 150 + 80; // 80-230px
            x += saccadeLength;
            
            // Variation verticale aléatoire (drift et micro-saccades)
            const verticalDrift = (Math.random() - 0.5) * 20;
            y += verticalDrift;
            
            // Garde Y dans les limites
            y = Math.max(15, Math.min(85, y));
            
            this.points.push({ x, y });
            
            // Fixation (petits mouvements sur place)
            const fixationDuration = Math.floor(Math.random() * 3) + 1;
            for (let i = 0; i < fixationDuration; i++) {
                x += Math.random() * 10 + 5;
                y += (Math.random() - 0.5) * 5; // Micro-mouvements
                y = Math.max(15, Math.min(85, y));
                this.points.push({ x, y });
            }
        }
    }

    // Convertit les points en courbe SVG lissée
    pointsToPath(points) {
        if (points.length < 2) return '';
        
        let path = `M ${points[0].x},${points[0].y}`;
        
        // Utilise des courbes de Bézier quadratiques pour un tracé plus fluide
        for (let i = 1; i < points.length - 1; i++) {
            const current = points[i];
            const next = points[i + 1];
            const midX = (current.x + next.x) / 2;
            const midY = (current.y + next.y) / 2;
            
            path += ` Q ${current.x},${current.y} ${midX},${midY}`;
        }
        
        // Dernier point
        const last = points[points.length - 1];
        path += ` L ${last.x},${last.y}`;
        
        return path;
    }

    // Anime le traçage progressif
    startDrawing() {
        console.log(`Démarrage du traçage de la courbe ${this.color} dans ${this.delay}ms`);
        setTimeout(() => {
            this.generateRealisticPath();
            console.log(`Courbe ${this.color}: ${this.points.length} points générés`);
            this.currentIndex = 0;
            this.isDrawing = true;
            this.animate();
        }, this.delay);
    }

    animate() {
        if (!this.isDrawing) return;
        
        // Vitesse réduite pour un traçage plus lent et visible
        const increment = Math.random() * 0.5 + 0.3; // 0.3-0.8 points par frame (plus lent)
        this.currentIndex += increment;
        
        if (this.currentIndex >= this.points.length) {
            // Animation terminée, fade out puis recommence
            this.fadeOut();
            return;
        }
        
        // Trace la courbe jusqu'au point actuel
        const visiblePoints = this.points.slice(0, Math.floor(this.currentIndex));
        this.pathString = this.pointsToPath(visiblePoints);
        this.path.setAttribute('d', this.pathString);
        
        // Continue l'animation avec un petit délai pour ralentir encore plus
        setTimeout(() => {
            requestAnimationFrame(() => this.animate());
        }, 16); // ~60fps mais avec délai pour effet plus visible
    }

    fadeOut() {
        let opacity = 0.9;
        const fadeInterval = setInterval(() => {
            opacity -= 0.05;
            this.path.style.opacity = opacity;
            
            if (opacity <= 0) {
                clearInterval(fadeInterval);
                this.path.setAttribute('d', '');
                this.path.style.opacity = 0.9;
                
                // Recommence après un court délai
                setTimeout(() => this.startDrawing(), 1000);
            }
        }, 50);
    }
}

// Initialise les courbes d'eye-tracking
window.initEyeTrackingCurves = () => {
    console.log('Initialisation des courbes d\'eye-tracking...');
    
    const svg = document.querySelector('.animated-curves');
    if (!svg) {
        console.error('SVG .animated-curves non trouvé !');
        return;
    }
    
    console.log('SVG trouvé:', svg);
    
    // Nettoie les anciennes instances si elles existent
    if (window.eyeTrackingCurvesInstances) {
        console.log('Nettoyage des anciennes instances...');
        window.eyeTrackingCurvesInstances.forEach(curve => {
            curve.isDrawing = false;
        });
    }
    
    // Plus de couleurs pour plus de courbes
    const colors = [
        '#ff6b6b', '#4ecdc4', '#ffe66d', '#95e1d3', '#f38181',
        '#a8e6cf', '#ffd3b6', '#ffaaa5', '#ff8b94', '#c7ceea'
    ];
    const curves = [];
    
    // Crée 10 courbes avec des délais échelonnés plus courts
    for (let i = 1; i <= 10; i++) {
        const path = document.querySelector(`.curve-${i}`);
        if (path) {
            console.log(`Courbe ${i} trouvée`);
            const curve = new EyeTrackingCurve(
                svg,
                path,
                colors[i - 1],
                i * 1500 // Délai de 1.5 secondes entre chaque courbe
            );
            curves.push(curve);
            curve.startDrawing();
        } else {
            console.error(`Courbe ${i} non trouvée !`);
        }
    }
    
    console.log(`${curves.length} courbes initialisées`);
    
    // Stocke les instances pour un éventuel nettoyage
    window.eyeTrackingCurvesInstances = curves;
    
    return curves;
};

// Auto-initialisation au chargement (pour les pages non-Blazor)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOMContentLoaded déclenché');
        window.initEyeTrackingCurves();
    });
} else if (document.readyState === 'complete' || document.readyState === 'interactive') {
    // Si le script est chargé après le DOMContentLoaded
    console.log('Document déjà chargé, initialisation immédiate');
    setTimeout(() => window.initEyeTrackingCurves(), 100);
}



