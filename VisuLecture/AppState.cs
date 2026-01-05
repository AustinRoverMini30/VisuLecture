using Microsoft.JSInterop;
using VisuLecture.Components;

namespace VisuLecture;

public class AppState
{
    private AppConfiguration _config = new AppConfiguration();
    
    private string _processingServerURI = "localhost:3000";
    public IJSRuntime JsRuntime { get; }
    private bool _initialized;


    public AppState(IJSRuntime jsRuntime)
    {
        JsRuntime = jsRuntime;
    }
    
}