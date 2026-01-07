using Microsoft.EntityFrameworkCore;
using Radzen;
using VisuLecture;
using VisuLecture.Components;
using VisuLecture.Components.Controller;

var builder = WebApplication.CreateBuilder(args);

// Lier Kestrel pour écouter toutes les interfaces (utile pour accéder depuis d'autres machines)
builder.WebHost.UseUrls("http://0.0.0.0:5188");

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

builder.Services.AddRadzenComponents();

//Permet d'accéder à AppState dans toute l'application grâce à une injection
//avec @inject AppState AppState
builder.Services.AddScoped<AppState>();
builder.Services.AddControllers();

builder.Services.AddSingleton<CalibrationService>();
builder.Services.AddHostedService(sp => sp.GetRequiredService<CalibrationService>());

builder.Services.AddDbContext<AppDbContext>(options =>
{
    options.UseSqlite("Data Source=app.db");
});

var app = builder.Build();

// Créer automatiquement la base de données au démarrage si elle n'existe pas
using (var scope = app.Services.CreateScope())
{
    var dbContext = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    try
    {
        // Crée la base de données et toutes les tables si elles n'existent pas
        dbContext.Database.EnsureCreated();
        Console.WriteLine("Base de données créée/vérifiée avec succès.");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Erreur lors de la création de la base de données : {ex.Message}");
    }
}

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();

app.UseStaticFiles();

app.UseAntiforgery();

app.MapControllers();
app.MapStaticAssets();
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();