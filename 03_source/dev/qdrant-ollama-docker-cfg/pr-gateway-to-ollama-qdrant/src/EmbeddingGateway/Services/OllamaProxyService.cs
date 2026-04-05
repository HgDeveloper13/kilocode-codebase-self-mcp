using System.Net.Http.Headers;
using Microsoft.Extensions.Options;

namespace EmbeddingGateway.Services;

/// <summary>
/// Implementation of IOllamaProxyService that forwards requests to Ollama.
/// Supports streaming responses for chat/generate/embed endpoints.
/// </summary>
public class OllamaProxyService : IOllamaProxyService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<OllamaProxyService> _logger;
    private readonly string _upstreamUrl;

    private static readonly string[] RestrictedResponseHeaders = new[]
    {
        "Transfer-Encoding",
        "Content-Length",
        "Connection",
        "Keep-Alive",
        "Upgrade",
        "Proxy-Connection",
        "Proxy-Authenticate",
        "Proxy-Authorization",
        "TE",
        "Trailer",
        "Host"
    };

    public OllamaProxyService(
        IOptionsMonitor<UpstreamServicesConfig> config,
        HttpClient httpClient,
        ILogger<OllamaProxyService> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
        _upstreamUrl = config.CurrentValue.Ollama;
    }

    public async Task<HttpResponseMessage> ForwardRequestAsync(
        HttpRequest request,
        CancellationToken cancellationToken = default)
    {
        var targetPath = GetTargetPath(request);
        var uri = $"{_upstreamUrl}{targetPath}{request.QueryString}";

        _logger.LogInformation("Forwarding {Method} request to Ollama: {Uri}", request.Method, uri);

        using var message = new HttpRequestMessage(
            new HttpMethod(request.Method),
            uri);

        // Copy request headers
        foreach (var header in request.Headers)
        {
            if (!message.Headers.TryAddWithoutValidation(header.Key, header.Value.ToArray()) &&
                !message.Content?.Headers.TryAddWithoutValidation(header.Key, header.Value.ToArray()) == true)
            {
                _logger.LogWarning("Failed to copy header: {Key}", header.Key);
            }
        }

        // Copy request body for methods that support it
        if (request.Method != HttpMethods.Get && request.Method != HttpMethods.Head)
        {
            message.Content = new StreamContent(request.Body);
            
            if (request.ContentType != null)
            {
                message.Content.Headers.ContentType = MediaTypeHeaderValue.Parse(request.ContentType);
            }
        }

        var response = await _httpClient.SendAsync(message, cancellationToken);

        _logger.LogInformation("Ollama responded with status: {StatusCode}", response.StatusCode);

        return response;
    }

    public async Task ForwardStreamingRequestAsync(
        HttpRequest request,
        HttpResponse response,
        CancellationToken cancellationToken = default)
    {
        var targetPath = GetTargetPath(request);
        var uri = $"{_upstreamUrl}{targetPath}{request.QueryString}";

        _logger.LogInformation("Forwarding streaming {Method} request to Ollama: {Uri}", request.Method, uri);

        using var message = new HttpRequestMessage(
            new HttpMethod(request.Method),
            uri);

        // Copy request headers
        foreach (var header in request.Headers)
        {
            if (!message.Headers.TryAddWithoutValidation(header.Key, header.Value.ToArray()) &&
                !message.Content?.Headers.TryAddWithoutValidation(header.Key, header.Value.ToArray()) == true)
            {
                _logger.LogWarning("Failed to copy header: {Key}", header.Key);
            }
        }

        // Copy request body for methods that support it
        if (request.Method != HttpMethods.Get && request.Method != HttpMethods.Head)
        {
            message.Content = new StreamContent(request.Body);
            
            if (request.ContentType != null)
            {
                message.Content.Headers.ContentType = MediaTypeHeaderValue.Parse(request.ContentType);
            }
        }

        // Use ResponseHeadersRead to enable streaming
        using var upstreamResponse = await _httpClient.SendAsync(
            message,
            HttpCompletionOption.ResponseHeadersRead,
            cancellationToken);

        // Copy response status
        response.StatusCode = (int)upstreamResponse.StatusCode;

        // Copy response headers
        foreach (var header in upstreamResponse.Headers)
        {
            if (!RestrictedResponseHeaders.Contains(header.Key, StringComparer.OrdinalIgnoreCase))
            {
                response.Headers[header.Key] = header.Value.ToArray();
            }
        }

        foreach (var header in upstreamResponse.Content.Headers)
        {
            if (!RestrictedResponseHeaders.Contains(header.Key, StringComparer.OrdinalIgnoreCase))
            {
                response.Headers[header.Key] = header.Value.ToArray();
            }
        }

        // Stream the response body
        await using var responseStream = await upstreamResponse.Content.ReadAsStreamAsync(cancellationToken);
        await responseStream.CopyToAsync(response.Body, cancellationToken);
        await response.Body.FlushAsync(cancellationToken);
    }

    private string GetTargetPath(HttpRequest request)
    {
        // Extract the path after /api/ollama
        var path = request.Path.Value ?? "/";
        const string prefix = "/api/ollama";
        
        if (path.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
        {
            return path[prefix.Length..];
        }
        
        return path;
    }
}

/// <summary>
/// Configuration class for upstream services.
/// </summary>
public class UpstreamServicesConfig
{
    public string Ollama { get; set; } = "http://ollama:11434";
    public string Qdrant { get; set; } = "http://qdrant:6333";
}
