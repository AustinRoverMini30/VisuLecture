using System.Collections.Concurrent;
using System.Diagnostics;
using System.Globalization;
using Microsoft.EntityFrameworkCore;
using VisuLecture.Components;
using VisuLecture.Components.Controller;
using VisuLecture.Components.Model;

public class CalibrationService : BackgroundService
{
    private readonly ILogger<CalibrationService> _logger;
    private readonly IServiceScopeFactory _scopeFactory;
    private const string ConfigFilePath = "calibration_config.txt";
    private const string CalibrationGaugeConfigFilePath = "calibration_gauge_config.txt";
    
    public string clientId = "";
    
    public readonly ConcurrentQueue<(string, string)> _queue = new();
    private readonly SemaphoreSlim _signal = new(0);
    private readonly ConcurrentDictionary<string, DateTime> _waitingCalibrations
        = new();
    private CancellationTokenSource cts;
    private List<PointGaze> gazePoints = new();
    
    public string calibrationModel = "none";
    public bool enableCalibrationGauge = true; // Activer la jauge par défaut
    
    public CalibrationService(ILogger<CalibrationService> logger, IServiceScopeFactory scopeFactory)
    {
        _logger = logger;
        _scopeFactory = scopeFactory;
        _logger.LogInformation("CalibrationService constructor called");
        
        // Charger le modèle de calibration depuis le fichier
        LoadCalibrationModel();
        
        // Charger la configuration de la jauge de calibration
        LoadCalibrationGaugeConfig();
    }
    public bool IsClientWaiting(string clientId)
    {
        return _waitingCalibrations.ContainsKey(clientId);
    }
    public void Enqueue(string clientId, string textRecordFilePath)
    {
        _logger.LogInformation($"Enqueue called for clientId: {clientId}");
        Console.WriteLine($"Enqueue called for clientId: {clientId}");
        
        if (!_waitingCalibrations.ContainsKey(clientId))
        {
            Console.WriteLine("clientId souhaité : " +  clientId);
            Console.WriteLine("Erreur, calibration non realisée");
            Console.WriteLine("Liste des clientId disponibles :");

            foreach (var id in _waitingCalibrations.Keys)
            {
                Console.WriteLine(" - " + id);
            }
            
            _logger.LogWarning($"ClientId {clientId} not found in waiting calibrations");
            return;
        }
        
        _queue.Enqueue((clientId, textRecordFilePath));
        _signal.Release(); // Réveille le consommateur
        
        _logger.LogInformation($"Task queued for clientId: {clientId}");
        Console.WriteLine($"Task queued for clientId: {clientId}, signal released");
    }
    
    /// <summary>
    /// Réanalyse les données d'une lecture existante
    /// </summary>
    public void EnqueueReanalysis(string clientId, string textRecordFilePath)
    {
        _logger.LogInformation($"EnqueueReanalysis called for clientId: {clientId}");
        Console.WriteLine($"EnqueueReanalysis called for clientId: {clientId}");
        
        // Pour la réanalyse, on ajoute directement à la queue sans vérifier _waitingCalibrations
        // car les vidéos existent déjà
        _queue.Enqueue((clientId, textRecordFilePath));
        _signal.Release(); // Réveille le consommateur
        
        _logger.LogInformation($"Reanalysis task queued for clientId: {clientId}");
        Console.WriteLine($"Reanalysis task queued for clientId: {clientId}, signal released");
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("CalibrationService ExecuteAsync STARTED");
        Console.WriteLine("CalibrationService ExecuteAsync STARTED");
        
        try
        {
            await StartProcessingAsync(stoppingToken);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error in ExecuteAsync");
            Console.WriteLine($"Error in ExecuteAsync: {ex.Message}");
        }
    }
    
   private async Task StartProcessingAsync(CancellationToken token)
    {
        _logger.LogInformation("StartProcessingAsync - Waiting for calibration tasks...");
        Console.WriteLine("StartProcessingAsync - Waiting for calibration tasks...");
        
        while (!token.IsCancellationRequested)
        {
            _logger.LogInformation("Waiting for signal...");
            await _signal.WaitAsync(token);

            _logger.LogInformation("Signal received! Processing task...");
            Console.WriteLine("Signal received! Processing task...");
            
            if (_queue.TryDequeue(out var action))
            {
                await HandleActionAsync(action, token);
            }
        }
    }

    private async Task HandleActionAsync((string, string) tuple, CancellationToken token)
    {
        clientId = tuple.Item1;
        var textRecordFilePath = tuple.Item2;
        
        _logger.LogInformation($"HandleActionAsync started for clientId: {clientId}");
        Console.WriteLine($"HandleActionAsync: Started processing for {clientId}");
        
        // Récupérer les dimensions depuis la base de données
        int screenWidth = 1920;
        int screenHeight = 1080;
        
        using (var scope = _scopeFactory.CreateScope())
        {
            var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
            var reading = await db.Readings.FirstOrDefaultAsync(r => r.Id == clientId);
            
            if (reading != null)
            {
                screenWidth = reading.ScreenWidth > 0 ? reading.ScreenWidth : 1920;
                screenHeight = reading.ScreenHeight > 0 ? reading.ScreenHeight : 1080;
                
                Console.WriteLine($"Dimensions d'écran récupérées: {screenWidth}x{screenHeight}");
                _logger.LogInformation($"Screen dimensions: {screenWidth}x{screenHeight}");
            }
            else
            {
                Console.WriteLine($"Reading non trouvée pour {clientId}, utilisation des dimensions par défaut");
                _logger.LogWarning($"Reading not found for {clientId}, using default dimensions");
            }
        }
        
        string pythonExe = "python3.11";
        string videoPrefix = $@"uploads/{clientId}/video"; // Préfixe pour video0.webm, video1.webm, etc.
        string calibScriptPath = @"Calibrate.py";
        string readScriptPath = @"Reading.py";
        string cleanDataScriptPath = @"clean_data.py";
        string pointsCsv = "records/" + clientId + "/raw.csv";
        string wordsCsv = "wwwroot/"+textRecordFilePath+"/resultats_ocr.csv";
        string outputCleanedCsv = "records/" + clientId + "/cleaned.csv";
        string outputNormalizedCsv = "records/" + clientId + "/normalized.csv";
        string outputSmoothedBothCsv = "records/" + clientId + "/smoothedBoth.csv";
        string outputSmoothedYCsv = "records/" + clientId + "/smoothedY.csv";
        
        // Exécuter le script de calibration Python avec le préfixe des vidéos
        Console.WriteLine($"Lancement de Calibrate.py pour {clientId}...");
        _logger.LogInformation($"Starting Calibrate.py for {clientId}");
        
        Console.WriteLine($"Modèle de calibration utilisé : {calibrationModel}");
        
        var calibProcess = new Process
        {
            StartInfo = new ProcessStartInfo
            {
                FileName = pythonExe,
                Arguments = $"\"{calibScriptPath}\" --video-prefix \"{videoPrefix}\" --calibration 9p --duration 5 --width {screenWidth} --height {screenHeight} --model {calibrationModel}",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            }
        };

        calibProcess.Start();
        
        // Afficher les logs Python pour le debug
        string output = await calibProcess.StandardOutput.ReadToEndAsync();
        string error = await calibProcess.StandardError.ReadToEndAsync();
        
        if (!string.IsNullOrEmpty(output))
        {
            Console.WriteLine($"Calibrate.py output: {output}");
            _logger.LogInformation($"Calibrate.py output: {output}");
        }
        if (!string.IsNullOrEmpty(error))
        {
            Console.WriteLine($"Calibrate.py error: {error}");
            _logger.LogError($"Calibrate.py error: {error}");
        }
            
        await calibProcess.WaitForExitAsync();
        Console.WriteLine($"Calibrate.py terminé avec code: {calibProcess.ExitCode}");
        _logger.LogInformation($"Calibrate.py finished with exit code: {calibProcess.ExitCode}");
        
        cts = new CancellationTokenSource();
        gazePoints.Clear();
        
        // Exécuter Reading.py
        Console.WriteLine($"Lancement de Reading.py pour {clientId}...");
        _logger.LogInformation($"Starting Reading.py for {clientId}");
        
        string videoPath = $@"uploads/{clientId}/reading.webm";
        await Process.Start(pythonExe, $"\"{readScriptPath}\" --video \"{videoPath}\" --csv \"{pointsCsv}\" --filter kde --width {screenWidth} --height {screenHeight} --model {calibrationModel}").WaitForExitAsync();
        
        Console.WriteLine($"Reading.py terminé pour {clientId}");
        _logger.LogInformation($"Reading.py finished for {clientId}");
        
        // Exécuter clean_data.py
        Console.WriteLine($"Lancement de clean_data.py pour {clientId}...");
        _logger.LogInformation($"Starting clean_data.py for {clientId}");
        
        await Process.Start(
            pythonExe,
            $"\"{cleanDataScriptPath}\" --points \"{pointsCsv}\" --words \"{wordsCsv}\" --cleaned \"{outputCleanedCsv}\" " +
            $"--normalized \"{outputNormalizedCsv}\" --smoothedBoth \"{outputSmoothedBothCsv}\" --smoothedY \"{outputSmoothedYCsv}\""
        ).WaitForExitAsync();

        Console.WriteLine($"clean_data.py terminé pour {clientId}");
        _logger.LogInformation($"clean_data.py finished for {clientId}");
        
        Console.WriteLine($"Traitement complet terminé pour {clientId}");
        _logger.LogInformation($"Complete processing finished for {clientId}");
        
        clientId = "";
    }
    
    public Task NotifyCalibrationCreation(string clientId)
    {
        _waitingCalibrations[clientId] = DateTime.Now;
        _logger.LogInformation($"NotifyCalibrationCreation called for clientId: {clientId}");
        Console.WriteLine($"NotifyCalibrationCreation: Added {clientId} to waiting calibrations");
        return Task.CompletedTask;
    }
    
    public static void SavePointsToCsv(List<PointGaze> points, string filePath, string fileName)
    {
        Directory.CreateDirectory(filePath);
        
        using (var writer = new StreamWriter(filePath+"/"+fileName))
        {
            // En-tête
            writer.WriteLine("index,x,y");

            // Lignes
            foreach (var p in points)
            {
                writer.WriteLine($"{p.timestamp.ToString(CultureInfo.InvariantCulture)},{p.x},{p.y}");
            }
        }
    }
    
    /// <summary>
    /// Sauvegarde le modèle de calibration dans un fichier texte
    /// </summary>
    public void SaveCalibrationModel()
    {
        try
        {
            File.WriteAllText(ConfigFilePath, calibrationModel);
            _logger.LogInformation($"Modèle de calibration sauvegardé : {calibrationModel}");
            Console.WriteLine($"Modèle de calibration sauvegardé dans {ConfigFilePath} : {calibrationModel}");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Erreur lors de la sauvegarde du modèle de calibration");
            Console.WriteLine($"Erreur lors de la sauvegarde du modèle de calibration : {ex.Message}");
        }
    }
    
    /// <summary>
    /// Charge le modèle de calibration depuis un fichier texte
    /// </summary>
    private void LoadCalibrationModel()
    {
        try
        {
            if (File.Exists(ConfigFilePath))
            {
                string loadedModel = File.ReadAllText(ConfigFilePath).Trim();
                
                // Valider que le modèle chargé est valide
                var validModels = new[] { "none", "elastic_net", "linear_svr", "ridge", "svr", "tiny_mlp" };
                if (validModels.Contains(loadedModel))
                {
                    calibrationModel = loadedModel;
                    _logger.LogInformation($"Modèle de calibration chargé : {calibrationModel}");
                    Console.WriteLine($"Modèle de calibration chargé depuis {ConfigFilePath} : {calibrationModel}");
                }
                else
                {
                    _logger.LogWarning($"Modèle invalide dans le fichier : {loadedModel}. Utilisation du modèle par défaut 'none'.");
                    Console.WriteLine($"Modèle invalide dans le fichier : {loadedModel}. Utilisation du modèle par défaut 'none'.");
                    calibrationModel = "none";
                }
            }
            else
            {
                _logger.LogInformation($"Fichier de configuration non trouvé. Utilisation du modèle par défaut : {calibrationModel}");
                Console.WriteLine($"Fichier de configuration non trouvé. Utilisation du modèle par défaut : {calibrationModel}");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Erreur lors du chargement du modèle de calibration");
            Console.WriteLine($"Erreur lors du chargement du modèle de calibration : {ex.Message}");
            calibrationModel = "none"; // Valeur par défaut en cas d'erreur
        }
    }

    /// <summary>
    /// Sauvegarde l'état de la jauge de calibration dans un fichier texte
    /// </summary>
    public void SaveCalibrationGaugeConfig()
    {
        try
        {
            File.WriteAllText(CalibrationGaugeConfigFilePath, enableCalibrationGauge.ToString());
            _logger.LogInformation($"Configuration de la jauge de calibration sauvegardée : {enableCalibrationGauge}");
            Console.WriteLine($"Configuration de la jauge sauvegardée dans {CalibrationGaugeConfigFilePath} : {enableCalibrationGauge}");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Erreur lors de la sauvegarde de la configuration de la jauge");
            Console.WriteLine($"Erreur lors de la sauvegarde de la configuration de la jauge : {ex.Message}");
        }
    }
    
    /// <summary>
    /// Charge l'état de la jauge de calibration depuis un fichier texte
    /// </summary>
    private void LoadCalibrationGaugeConfig()
    {
        try
        {
            if (File.Exists(CalibrationGaugeConfigFilePath))
            {
                string loadedConfig = File.ReadAllText(CalibrationGaugeConfigFilePath).Trim();
                
                if (bool.TryParse(loadedConfig, out bool gaugeEnabled))
                {
                    enableCalibrationGauge = gaugeEnabled;
                    _logger.LogInformation($"Configuration de la jauge de calibration chargée : {enableCalibrationGauge}");
                    Console.WriteLine($"Configuration de la jauge chargée depuis {CalibrationGaugeConfigFilePath} : {enableCalibrationGauge}");
                }
                else
                {
                    _logger.LogWarning($"Valeur invalide dans le fichier : {loadedConfig}. Utilisation de la valeur par défaut 'true'.");
                    Console.WriteLine($"Valeur invalide dans le fichier : {loadedConfig}. Utilisation de la valeur par défaut 'true'.");
                    enableCalibrationGauge = true;
                }
            }
            else
            {
                _logger.LogInformation($"Fichier de configuration de la jauge non trouvé. Utilisation de la valeur par défaut : {enableCalibrationGauge}");
                Console.WriteLine($"Fichier de configuration de la jauge non trouvé. Utilisation de la valeur par défaut : {enableCalibrationGauge}");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Erreur lors du chargement de la configuration de la jauge");
            Console.WriteLine($"Erreur lors du chargement de la configuration de la jauge : {ex.Message}");
            enableCalibrationGauge = true; // Valeur par défaut en cas d'erreur
        }
    }

    
}
