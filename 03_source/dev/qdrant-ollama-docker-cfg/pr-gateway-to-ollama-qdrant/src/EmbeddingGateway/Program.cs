using EmbeddingGateway.Endpoints;
using EmbeddingGateway.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddOpenApi();

// Configure upstream services from appsettings.json
builder.Services.Configure<UpstreamServicesConfig>(
    builder.Configuration.GetSection("UpstreamServices"));

// Add HttpClient for Ollama
builder.Services.AddHttpClient<IOllamaProxyService, OllamaProxyService>(client =>
{
    client.Timeout = TimeSpan.FromMinutes(10); // Long timeout for LLM responses
});

// Add HttpClient for Qdrant
builder.Services.AddHttpClient<IQdrantProxyService, QdrantProxyService>(client =>
{
    client.Timeout = TimeSpan.FromMinutes(5);
});

// Add CORS if needed
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseCors();

// Map health check endpoint
app.MapGet("/health", async (
    IHttpClientFactory httpClientFactory,
    IConfiguration configuration) =>
{
    var ollamaUrl = configuration["UpstreamServices:Ollama"] ?? "http://ollama:11434";
    var qdrantUrl = configuration["UpstreamServices:Qdrant"] ?? "http://qdrant:6333";
    
    var httpClient = httpClientFactory.CreateClient();
    httpClient.Timeout = TimeSpan.FromSeconds(5);
    
    var ollamaHealthy = await CheckServiceHealthAsync(httpClient, ollamaUrl);
    var qdrantHealthy = await CheckServiceHealthAsync(httpClient, qdrantUrl);
    
    var status = ollamaHealthy && qdrantHealthy 
        ? Results.Ok(new 
        { 
            status = "healthy", 
            services = new 
            { 
                ollama = new { status = ollamaHealthy ? "healthy" : "unhealthy", url = ollamaUrl },
                qdrant = new { status = qdrantHealthy ? "healthy" : "unhealthy", url = qdrantUrl }
            }
        })
        : Results.StatusCode(503);
    
    return status;
});

async Task<bool> CheckServiceHealthAsync(HttpClient client, string baseUrl)
{
    try
    {
        var response = await client.GetAsync($"{baseUrl}/");
        return response.IsSuccessStatusCode;
    }
    catch
    {
        return false;
    }
}

// Map proxy endpoints
app.MapOllamaProxyEndpoints();
app.MapQdrantProxyEndpoints();

app.Run();
