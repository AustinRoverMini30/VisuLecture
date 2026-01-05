using System.Collections.Concurrent;
using System.Diagnostics;
using System.Drawing.Printing;
using System.Globalization;
using System.Threading;
using System.Threading.Tasks;
using Eyeware.BeamEyeTracker;
using VisuLecture.Components;

public class CalibrationService : BackgroundService
{
    
    public string clientId = "";
    
    public readonly ConcurrentQueue<(string, string)> _queue = new();
    private readonly SemaphoreSlim _signal = new(0);
    private readonly ConcurrentDictionary<string, DateTime> _waitingCalibrations
        = new();
    private CancellationTokenSource cts;
    private List<PointGaze> gazePoints = new();
    public bool IsClientWaiting(string clientId)
    {
        return _waitingCalibrations.ContainsKey(clientId);
    }
    public void Enqueue(string clientId, string textRecordFilePath)
    {
        if (!_waitingCalibrations.ContainsKey(clientId))
        {
            Console.WriteLine("clientId souhaité : " +  clientId);
            Console.WriteLine("Erreur, calibration non realisée");
            Console.WriteLine("Liste des clientId disponibles :");

            foreach (var id in _waitingCalibrations.Keys)
            {
                Console.WriteLine(" - " + id);
            }
            return;
        }
        _queue.Enqueue((clientId, textRecordFilePath));
        _signal.Release(); // Réveille le consommateur
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await StartProcessingAsync(stoppingToken);
    }
    
   private async Task StartProcessingAsync(CancellationToken token)
    {
        while (!token.IsCancellationRequested)
        {
            await _signal.WaitAsync(token);

            if (_queue.TryDequeue(out var action))
                await HandleActionAsync(action, token);
        }
    }

    private async Task HandleActionAsync((string, string) tuple, CancellationToken token)
    {
        
        clientId = tuple.Item1;
        var textRecordFilePath = tuple.Item2;
        
        Console.WriteLine("Started new action");
        string pythonExe = "python";
        string videoPath = $@"uploads\{clientId}\\";
        string calibScriptPath = @"Calibrate.py";
        string readScriptPath = @"Reading.py";
        string cleanDataScriptPath = @"clean_data.py";
        string pointsCsv = "records/" + clientId;
        string wordsCsv = "wwwroot/"+textRecordFilePath+"/resultats_ocr.csv";
        string outputCsv = "records/" + clientId + "/cleaned.csv";
        var process = new Process
        {
            StartInfo = new ProcessStartInfo
            {
                FileName = pythonExe,
                Arguments = $"\"{calibScriptPath}\" \"{videoPath}\" 30",
                UseShellExecute = false
            }
        };

        process.Start();
            
        await process.WaitForExitAsync(token);
        cts = new CancellationTokenSource();
        gazePoints.Clear();
        
        Task.Run(() => getGazePoints(cts.Token));
        
        await Process.Start(pythonExe, $"\"{readScriptPath}\" \"{videoPath}\" 30").WaitForExitAsync();
        
        cts.Cancel();
        SavePointsToCsv(gazePoints, "records/" + clientId, "raw.csv");
        
        await Process.Start(
            pythonExe,
            $"\"{cleanDataScriptPath}\" -p \"{pointsCsv}\" -w \"{wordsCsv}\" -o \"{outputCsv}\""
        ).WaitForExitAsync();

        clientId = "";
    }
    
    public Task NotifyCalibrationCreation(string clientId)
    {
        _waitingCalibrations[clientId] = DateTime.Now;
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
    
    public void getGazePoints(CancellationToken token)
    {
        var viewport = new ViewportGeometry();
        Console.WriteLine("Viewport 11" + viewport.Point11.Y);
        var api = new Eyeware.BeamEyeTracker.API("testC#", viewport);
        var timestamp = -1.0;
        var cleanFirstElement = true;
        
        while (!token.IsCancellationRequested)
        {
            var temp = api.GetLatestTrackingStateSet().UserState;
            if (temp.TimestampInSeconds != -1 && temp.UnifiedScreenGaze.Confidence == TrackingConfidence.High)
            {
                if (cleanFirstElement && temp.UnifiedScreenGaze.PointOfRegard.Y < 500)
                {
                    cleanFirstElement = false;
                }
                if (!cleanFirstElement)
                {
                    gazePoints.Add(new PointGaze(temp.TimestampInSeconds, temp.UnifiedScreenGaze.PointOfRegard.X, temp.UnifiedScreenGaze.PointOfRegard.Y));
                }
            }
            api.WaitForNewTrackingData(ref timestamp, 1000);
        }
    }

    
}

