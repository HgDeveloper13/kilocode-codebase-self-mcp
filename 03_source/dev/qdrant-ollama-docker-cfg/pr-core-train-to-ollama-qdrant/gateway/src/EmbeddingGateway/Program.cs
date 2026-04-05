using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using StackExchange.Redis;

var builder = WebApplication.CreateBuilder(args);

// Configuration
var ollamaUrl = builder.Configuration["Ollama:Url"] ?? "http://ollama:11434";
var redisHost = builder.Configuration["Redis:Host"] ?? "redis";
var redisPort = builder.Configuration["Redis:Port"] ?? "6379";

// Register HttpClient for Ollama
builder.Services.AddHttpClient("Ollama", client =>
{
    client.BaseAddress = new Uri(ollamaUrl);
    client.Timeout = TimeSpan.FromMinutes(5);
});

// Register Redis
builder.Services.AddSingleton<IConnectionMultiplexer>(sp =>
{
    var config = $"{redisHost}:{redisPort}";
    return ConnectionMultiplexer.Connect(config);
});

var app = builder.Build();

// Health check endpoint
app.MapGet("/health", async (IConnectionMultiplexer redis, HttpClient httpClient) =>
{
    var redisStatus = redis.IsConnected ? "connected" : "disconnected";
    
    string ollamaStatus;
    try
    {
        var response = await httpClient.GetAsync("/api/tags");
        ollamaStatus = response.IsSuccessStatusCode ? "available" : "unavailable";
    }
    catch
    {
        ollamaStatus = "unavailable";
    }

    var status = redisStatus == "connected" && ollamaStatus == "available" 
        ? Results.Ok(new { redis = redisStatus, ollama = ollamaStatus })
        : Results.StatusCode(503);
    
    return status;
});

// Embed endpoint with Redis caching
app.MapPost("/api/embed", async (HttpContext context, IConnectionMultiplexer redis, HttpClient ollamaClient) =>
{
    var body = await new StreamReader(context.Request.Body).ReadToEndAsync();
    
    // Generate cache key from request body
    var cacheKey = GenerateCacheKey(body);
    
    // Try to get from Redis cache
    var db = redis.GetDatabase();
    var cachedResult = await db.StringGetAsync(cacheKey);
    
    if (cachedResult.HasValue)
    {
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsync(cachedResult!);
        return;
    }
    
    // Cache miss - forward to Ollama
    var content = new StringContent(body, Encoding.UTF8, "application/json");
    var response = await ollamaClient.PostAsync("/api/embed", content);
    var responseContent = await response.Content.ReadAsStringAsync();
    
    if (response.IsSuccessStatusCode)
    {
        // Store in Redis cache (7 days TTL)
        await db.StringSetAsync(cacheKey, responseContent, TimeSpan.FromDays(7));
    }
    
    context.Response.ContentType = "application/json";
    context.Response.StatusCode = (int)response.StatusCode;
    await context.Response.WriteAsync(responseContent);
});

// Embeddings endpoint with Redis caching
app.MapPost("/api/embeddings", async (HttpContext context, IConnectionMultiplexer redis, HttpClient ollamaClient) =>
{
    var body = await new StreamReader(context.Request.Body).ReadToEndAsync();
    
    // Generate cache key from request body
    var cacheKey = GenerateCacheKey(body);
    
    // Try to get from Redis cache
    var db = redis.GetDatabase();
    var cachedResult = await db.StringGetAsync(cacheKey);
    
    if (cachedResult.HasValue)
    {
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsync(cachedResult!);
        return;
    }
    
    // Cache miss - forward to Ollama
    var content = new StringContent(body, Encoding.UTF8, "application/json");
    var response = await ollamaClient.PostAsync("/api/embeddings", content);
    var responseContent = await response.Content.ReadAsStringAsync();
    
    if (response.IsSuccessStatusCode)
    {
        // Store in Redis cache (7 days TTL)
        await db.StringSetAsync(cacheKey, responseContent, TimeSpan.FromDays(7));
    }
    
    context.Response.ContentType = "application/json";
    context.Response.StatusCode = (int)response.StatusCode;
    await context.Response.WriteAsync(responseContent);
});

// Helper method to generate SHA256 cache key
static string GenerateCacheKey(string input)
{
    var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(input));
    var hash = Convert.ToHexString(bytes).ToLowerInvariant();
    return $"emb:{hash}";
}

app.Run();
