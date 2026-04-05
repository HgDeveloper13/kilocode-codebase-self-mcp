namespace EmbeddingGateway.Services;

/// <summary>
/// Interface for proxying requests to Qdrant vector database service.
/// Forwards all HTTP methods (GET, POST, PUT, DELETE, PATCH).
/// </summary>
public interface IQdrantProxyService
{
    /// <summary>
    /// Forwards a request to Qdrant and streams the response back.
    /// </summary>
    Task ForwardRequestAsync(
        HttpRequest request,
        HttpResponse response,
        CancellationToken cancellationToken = default);
}
