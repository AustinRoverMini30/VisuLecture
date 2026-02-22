namespace VisuLecture.Components.Model;

public class CalibrationErrorLog
{
    public string ClientId { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; }
    public string ErrorMessage { get; set; } = string.Empty;
    public string StackTrace { get; set; } = string.Empty;
    
    public CalibrationErrorLog() { }
    
    public CalibrationErrorLog(string clientId, string errorMessage, string stackTrace = "")
    {
        ClientId = clientId;
        Timestamp = DateTime.Now;
        ErrorMessage = errorMessage;
        StackTrace = stackTrace;
    }
}

