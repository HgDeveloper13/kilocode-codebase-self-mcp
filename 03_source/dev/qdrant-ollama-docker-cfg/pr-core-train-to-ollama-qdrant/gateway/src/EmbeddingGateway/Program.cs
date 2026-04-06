using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using StackExchange.Redis;

var builder = WebApplication.CreateBuilder(args);

// Configuration
var ollamaUrl = builder.Configuration["Ollama:Url"] ?? "http://ollama:11434";
var redisHost = builder.Configuration["Redis:Host"] ?? "redis";
var redisPort = builder.Configuration["Redis:Port"] ?? "6379";

// Register IHttpClientFactory for Ollama (CORRECT WAY)
builder.Services.AddHttpClient();

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

// Embed endpoint with Redis caching (native Ollama API)
app.MapPost("/api/embed", async (HttpContext context, IConnectionMultiplexer redis, IHttpClientFactory httpClientFactory) =>
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
    
    // Cache miss - forward to Ollama (native API)
    var ollamaClient = httpClientFactory.CreateClient();
    ollamaClient.BaseAddress = new Uri(ollamaUrl);
    ollamaClient.Timeout = TimeSpan.FromMinutes(5);
    
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

// Embeddings endpoint with Redis caching (native Ollama API)
app.MapPost("/api/embeddings", async (HttpContext context, IConnectionMultiplexer redis, IHttpClientFactory httpClientFactory) =>
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
    
    // Cache miss - forward to Ollama (native API)
    var ollamaClient = httpClientFactory.CreateClient();
    ollamaClient.BaseAddress = new Uri(ollamaUrl);
    ollamaClient.Timeout = TimeSpan.FromMinutes(5);
    
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

// OpenAI-compatible /v1/embeddings endpoint (NEW!)
app.MapPost("/v1/embeddings", async (HttpContext context, IConnectionMultiplexer redis, IHttpClientFactory httpClientFactory) =>
{
    var body = await new StreamReader(context.Request.Body).ReadToEndAsync();
    
    // Generate cache key from request body
    var cacheKey = GenerateCacheKey(body);
    
    // Try to get from Redis cache
    var db = redis.GetDatabase();
    var cachedResult = await db.StringGetAsync(cacheKey);
    
    if (cachedResult.HasValue)
    {
        // Convert response from native format to OpenAI format if needed
        await WriteOpenAiResponse(context, cachedResult!, body);
        return;
    }
    
    // Cache miss - convert from OpenAI format to native format for Ollama
    var nativeRequest = ConvertToNativeFormat(body);
    
    var ollamaClient = httpClientFactory.CreateClient();
    ollamaClient.BaseAddress = new Uri(ollamaUrl);
    ollamaClient.Timeout = TimeSpan.FromMinutes(5);
    
    var content = new StringContent(nativeRequest, Encoding.UTF8, "application/json");
    var response = await ollamaClient.PostAsync("/api/embed", content);
    var responseContent = await response.Content.ReadAsStringAsync();
    
    if (response.IsSuccessStatusCode)
    {
        // Store in Redis cache (7 days TTL)
        await db.StringSetAsync(cacheKey, responseContent, TimeSpan.FromDays(7));
    }
    
    // Convert response to OpenAI format
    await WriteOpenAiResponse(context, responseContent, body);
});

// Helper method to convert OpenAI format request to native Ollama format
static string ConvertToNativeFormat(string openAiRequest)
{
    try
    {
        using var doc = JsonDocument.Parse(openAiRequest);
        var root = doc.RootElement;
        
        // Extract model name
        string model = "";
        if (root.TryGetProperty("model", out var modelProp))
        {
            model = modelProp.GetString() ?? "";
        }
        
        // Extract input text(s)
        string input = "";
        if (root.TryGetProperty("input", out var inputProp))
        {
            if (inputProp.ValueKind == JsonValueKind.String)
            {
                input = inputProp.GetString() ?? "";
            }
            else if (inputProp.ValueKind == JsonValueKind.Array)
            {
                // Take first element if array
                var firstElement = inputProp[0];
                input = firstElement.GetString() ?? "";
            }
        }
        
        // Create native format
        var nativeFormat = new { model = model, input = input };
        return JsonSerializer.Serialize(nativeFormat);
    }
    catch
    {
        // Return as-is if parsing fails
        return openAiRequest;
    }
}

// Helper method to convert native Ollama response to OpenAI format
static async Task WriteOpenAiResponse(HttpContext context, string nativeResponse, string originalRequest)
{
    try
    {
        using var doc = JsonDocument.Parse(nativeResponse);
        var root = doc.RootElement;
        
        // Extract model name
        string modelName = "";
        if (root.TryGetProperty("model", out var modelProp))
        {
            modelName = modelProp.GetString() ?? "";
        }
        
        // Extract embeddings from native response
        var embeddings = new List<List<float>>();
        if (root.TryGetProperty("embeddings", out var embProp) && embProp.ValueKind == JsonValueKind.Array)
        {
            foreach (var emb in embProp.EnumerateArray())
            {
                var floatList = new List<float>();
                foreach (var val in emb.EnumerateArray())
                {
                    floatList.Add((float)val.GetDouble());
                }
                embeddings.Add(floatList);
            }
        }
        
        // Create OpenAI format response
        var openAiResponse = new
        {
            @object = "embedding",
            data = embeddings.Select((emb, idx) => new
            {
                @object = "embedding",
                embedding = emb,
                index = idx
            }).ToList(),
            model = modelName,
            usage = new
            {
                prompt_tokens = 0,
                total_tokens = 0
            }
        };
        
        context.Response.ContentType = "application/json";
        context.Response.StatusCode = 200;
        await context.Response.WriteAsync(JsonSerializer.Serialize(openAiResponse));
    }
    catch
    {
        // Return native response as-is if conversion fails
        context.Response.ContentType = "application/json";
        context.Response.StatusCode = 200;
        await context.Response.WriteAsync(nativeResponse);
    }
}

// Helper method to generate SHA256 cache key
static string GenerateCacheKey(string input)
{
    var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(input));
    var hash = Convert.ToHexString(bytes).ToLowerInvariant();
    return $"emb:{hash}";
}

app.Run();
