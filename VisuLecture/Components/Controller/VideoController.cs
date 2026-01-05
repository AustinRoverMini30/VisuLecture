namespace VisuLecture.Components.Controller;

using Microsoft.AspNetCore.Mvc;

[ApiController]
[Route("api/[controller]")]
public class VideoController : ControllerBase
{
    private readonly IWebHostEnvironment _env;
    private readonly ILogger<VideoController> _log;

    public VideoController(IWebHostEnvironment env, ILogger<VideoController> log)
    {
        _env = env;
        _log = log;
    }

    [HttpPost("upload")]
    [RequestSizeLimit(200_000_000)] // 200 MB example - ou configurer Kestrel/globalement
    public async Task<IActionResult> Upload(IFormFile file, CancellationToken ct)
    {
        if (file == null || file.Length == 0) return BadRequest("No file");

        // validation basique
        if (!file.ContentType.Contains("webm") && !file.ContentType.Contains("mp4") && !file.ContentType.Contains("octet-stream"))
        {
            return BadRequest("Type non supporté");
        }

        string clientId = Request.Form["client-id"].ToString() ?? "";
        
        var tmpDir = Path.Combine(_env.ContentRootPath, "uploads");
        var clientDir =  Path.Combine(tmpDir, clientId);
        Directory.CreateDirectory(clientDir);
        var fileName = file.FileName;
        var fullPath = Path.Combine(clientDir, fileName);

        await using (var fs = System.IO.File.Create(fullPath))
        {
            await file.CopyToAsync(fs, ct);
        }

        _log.LogInformation("Fichier reçu: {File} ({Len} bytes)", fileName, file.Length);

        // Lancer traitement en arrière-plan (ex: FFmpeg) - simple exemple synchrone (déconseillé pour grosses tâches)
        // But better: mettre dans queue et traiter par BackgroundService.
        // Exemple: return Accepted et planifier traitement
        // Pour l'exemple, on renvoie le chemin relatif
        return Ok(new { path = fullPath, fileName });
    }
}