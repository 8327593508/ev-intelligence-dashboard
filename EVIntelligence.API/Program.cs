using Microsoft.Extensions.FileProviders;
using DotNetEnv;

var builder = WebApplication.CreateBuilder(args);

// Load .env
Env.Load();

builder.Services.AddControllers();
builder.Services.AddHttpClient();

var app = builder.Build();

// ⭐ ABSOLUTE PATH TO FRONTEND FOLDER
var frontendPath = Path.Combine(builder.Environment.ContentRootPath, "frontend");

// Enable default files (ai.html, index.html)
app.UseDefaultFiles(new DefaultFilesOptions
{
    FileProvider = new PhysicalFileProvider(frontendPath),
    DefaultFileNames = new List<string> { "index.html", "ai.html" }
});

// Serve static files (CSS, JS, HTML)
app.UseStaticFiles(new StaticFileOptions
{
    FileProvider = new PhysicalFileProvider(frontendPath),
    RequestPath = ""
});

app.UseRouting();
app.MapControllers();

app.Run();