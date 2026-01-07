window.getWindowSize = () => {
    return {
        width: screen.width,
        height: screen.height,
    };
};

// Fonction pour télécharger un fichier depuis une chaîne base64
window.downloadFile = (fileName, base64Content) => {
    const link = document.createElement('a');
    link.href = 'data:text/csv;charset=utf-8;base64,' + base64Content;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

