using System.Net.Http.Headers;
using Microsoft.Extensions.Options;

namespace EmbeddingGateway.Services;

/// <summary>
/// Implementation of IQdrantProxyService that forwards requests to Qdrant.
/// Supports all HTTP methods (GET, POST, PUT, DELETE, PATCH).
/// </summary>
public class QdrantProxyService : IQdrantProxyService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<QdrantProxyService> _logger;
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

    public QdrantProxyService(
        IOptionsMonitor<UpstreamServicesConfig> config,
        HttpClient httpClient,
        ILogger<QdrantProxyService> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
        _upstreamUrl = config.CurrentValue.Qdrant;
    }

    public async Task ForwardRequestAsync(
        HttpRequest request,
        HttpResponse response,
        CancellationToken cancellationToken = default)
    {
        var targetPath = GetTargetPath(request);
        var uri = $"{_upstreamUrl}{targetPath}{request.QueryString}";

        _logger.LogInformation("Forwarding {Method} request to Qdrant: {Uri}", request.Method, uri);

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
        // Extract the path after /api/qdrant
        var path = request.Path.Value ?? "/";
        const string prefix = "/api/qdrant";
        
        if (path.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
        {
            return path[prefix.Length..];
        }
        
        return path;
    }
}
