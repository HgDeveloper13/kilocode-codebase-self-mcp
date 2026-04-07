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

// Constants for cache settings (moved to class level for static function access)
const int CacheTtlDays = 7;
const int InProgressTtlSeconds = 300; // 5 minutes max for processing
const int PollIntervalMs = 2000; // Poll every 2 seconds
const int MaxWaitTimeSeconds = 300; // Max wait 5 minutes

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

// Embed endpoint with Redis caching AND wait-for-cache mechanism (native Ollama API)
app.MapPost("/api/embed", async (HttpContext context, IConnectionMultiplexer redis, IHttpClientFactory httpClientFactory) =>
{
    var body = await new StreamReader(context.Request.Body).ReadToEndAsync();
    var cacheKey = GenerateCacheKey(body);
    
    var db = redis.GetDatabase();
    
    // Try to get from Redis cache
    var cachedResult = await db.StringGetAsync(cacheKey);
    
    if (cachedResult.HasValue)
    {
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsync(cachedResult!);
        return;
    }
    
    // Cache miss - check if another client is already processing this request
    var inProgressKey = $"in-progress:{cacheKey}";
    var inProgress = await db.StringGetAsync(inProgressKey);
    
    if (inProgress.HasValue)
    {
        // Another client is processing - wait for cache to be ready
        await WaitForCacheAsync(context, db, cacheKey, inProgressKey);
        return;
    }
    
    // This client will process the request
    // Set in-progress flag (expires in 5 minutes)
    await db.StringSetAsync(inProgressKey, "1", TimeSpan.FromSeconds(InProgressTtlSeconds));
    
    try
    {
        var ollamaClient = httpClientFactory.CreateClient();
        ollamaClient.BaseAddress = new Uri(ollamaUrl);
        ollamaClient.Timeout = TimeSpan.FromMinutes(5);
        
        var content = new StringContent(body, Encoding.UTF8, "application/json");
        var response = await ollamaClient.PostAsync("/api/embed", content);
        var responseContent = await response.Content.ReadAsStringAsync();
        
        if (response.IsSuccessStatusCode)
        {
            // Store in Redis cache (7 days TTL)
            await db.StringSetAsync(cacheKey, responseContent, TimeSpan.FromDays(CacheTtlDays));
        }
        
        context.Response.ContentType = "application/json";
        context.Response.StatusCode = (int)response.StatusCode;
        await context.Response.WriteAsync(responseContent);
    }
    finally
    {
        // Remove in-progress flag
        await db.KeyDeleteAsync(inProgressKey);
    }
});

// Embeddings endpoint with Redis caching AND wait-for-cache mechanism (native Ollama API)
app.MapPost("/api/embeddings", async (HttpContext context, IConnectionMultiplexer redis, IHttpClientFactory httpClientFactory) =>
{
    var body = await new StreamReader(context.Request.Body).ReadToEndAsync();
    var cacheKey = GenerateCacheKey(body);
    
    var db = redis.GetDatabase();
    
    // Try to get from Redis cache
    var cachedResult = await db.StringGetAsync(cacheKey);
    
    if (cachedResult.HasValue)
    {
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsync(cachedResult!);
        return;
    }
    
    // Cache miss - check if another client is already processing this request
    var inProgressKey = $"in-progress:{cacheKey}";
    var inProgress = await db.StringGetAsync(inProgressKey);
    
    if (inProgress.HasValue)
    {
        // Another client is processing - wait for cache to be ready
        await WaitForCacheAsync(context, db, cacheKey, inProgressKey);
        return;
    }
    
    // This client will process the request
    await db.StringSetAsync(inProgressKey, "1", TimeSpan.FromSeconds(InProgressTtlSeconds));
    
    try
    {
        var ollamaClient = httpClientFactory.CreateClient();
        ollamaClient.BaseAddress = new Uri(ollamaUrl);
        ollamaClient.Timeout = TimeSpan.FromMinutes(5);
        
        var content = new StringContent(body, Encoding.UTF8, "application/json");
        var response = await ollamaClient.PostAsync("/api/embeddings", content);
        var responseContent = await response.Content.ReadAsStringAsync();
        
        if (response.IsSuccessStatusCode)
        {
            await db.StringSetAsync(cacheKey, responseContent, TimeSpan.FromDays(CacheTtlDays));
        }
        
        context.Response.ContentType = "application/json";
        context.Response.StatusCode = (int)response.StatusCode;
        await context.Response.WriteAsync(responseContent);
    }
    finally
    {
        await db.KeyDeleteAsync(inProgressKey);
    }
});

// OpenAI-compatible /v1/embeddings endpoint with wait-for-cache mechanism
app.MapPost("/v1/embeddings", async (HttpContext context, IConnectionMultiplexer redis, IHttpClientFactory httpClientFactory) =>
{
    var body = await new StreamReader(context.Request.Body).ReadToEndAsync();
    var cacheKey = GenerateCacheKey(body);
    
    var db = redis.GetDatabase();
    
    // Try to get from Redis cache
    var cachedResult = await db.StringGetAsync(cacheKey);
    
    if (cachedResult.HasValue)
    {
        await WriteOpenAiResponse(context, cachedResult!, body);
        return;
    }
    
    // Cache miss - check if another client is already processing this request
    var inProgressKey = $"in-progress:{cacheKey}";
    var inProgress = await db.StringGetAsync(inProgressKey);
    
    if (inProgress.HasValue)
    {
        // Another client is processing - wait for cache to be ready
        await WaitForCacheAsync(context, db, cacheKey, inProgressKey);
        return;
    }
    
    // This client will process the request
    await db.StringSetAsync(inProgressKey, "1", TimeSpan.FromSeconds(InProgressTtlSeconds));
    
    try
    {
        // Convert from OpenAI format to native format
        var nativeRequest = ConvertToNativeFormat(body);
        
        var ollamaClient = httpClientFactory.CreateClient();
        ollamaClient.BaseAddress = new Uri(ollamaUrl);
        ollamaClient.Timeout = TimeSpan.FromMinutes(5);
        
        var content = new StringContent(nativeRequest, Encoding.UTF8, "application/json");
        var response = await ollamaClient.PostAsync("/api/embed", content);
        var responseContent = await response.Content.ReadAsStringAsync();
        
        if (response.IsSuccessStatusCode)
        {
            await db.StringSetAsync(cacheKey, responseContent, TimeSpan.FromDays(CacheTtlDays));
        }
        
        await WriteOpenAiResponse(context, responseContent, body);
    }
    finally
    {
        await db.KeyDeleteAsync(inProgressKey);
    }
});

// Helper method to wait for cache to be ready (poll mechanism) - using const parameters
static async Task WaitForCacheAsync(HttpContext context, IDatabase db, string cacheKey, string inProgressKey)
{
    var startTime = DateTime.UtcNow;
    var maxWaitTime = TimeSpan.FromSeconds(MaxWaitTimeSeconds);
    const int pollInterval = PollIntervalMs;
    const int maxWait = MaxWaitTimeSeconds;
    
    while (DateTime.UtcNow - startTime < maxWaitTime)
    {
        // Check if client disconnected
        if (context.RequestAborted.IsCancellationRequested)
        {
            context.Response.StatusCode = 499; // Client closed request
            return;
        }
        
        // Check if in-progress flag is still set (another client is still processing)
        var inProgress = await db.StringGetAsync(inProgressKey);
        if (!inProgress.HasValue)
        {
            // Processing done - check cache
            var cachedResult = await db.StringGetAsync(cacheKey);
            if (cachedResult.HasValue)
            {
                context.Response.ContentType = "application/json";
                await context.Response.WriteAsync(cachedResult!);
                return;
            }
        }
        
        // Wait before next poll
        await Task.Delay(pollInterval);
    }
    
    // Timeout - return whatever we have or error
    var finalCachedResult = await db.StringGetAsync(cacheKey);
    if (finalCachedResult.HasValue)
    {
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsync(finalCachedResult!);
    }
    else
    {
        context.Response.StatusCode = 504; // Gateway Timeout
        await context.Response.WriteAsync("{\"error\": \"Cache wait timeout\"}");
    }
}

// Helper method to convert OpenAI format request to native Ollama format
static string ConvertToNativeFormat(string openAiRequest)
{
    try
    {
        using var doc = JsonDocument.Parse(openAiRequest);
        var root = doc.RootElement;
        
        string model = "";
        if (root.TryGetProperty("model", out var modelProp))
        {
            model = modelProp.GetString() ?? "";
        }
        
        string input = "";
        if (root.TryGetProperty("input", out var inputProp))
        {
            if (inputProp.ValueKind == JsonValueKind.String)
            {
                input = inputProp.GetString() ?? "";
            }
            else if (inputProp.ValueKind == JsonValueKind.Array)
            {
                var firstElement = inputProp[0];
                input = firstElement.GetString() ?? "";
            }
        }
        
        var nativeFormat = new { model = model, input = input };
        return JsonSerializer.Serialize(nativeFormat);
    }
    catch
    {
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
        
        string modelName = "";
        if (root.TryGetProperty("model", out var modelProp))
        {
            modelName = modelProp.GetString() ?? "";
        }
        
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