namespace EmbeddingGateway.Services;

/// <summary>
/// Interface for proxying requests to Ollama service.
/// Supports streaming responses for chat/generate endpoints.
/// </summary>
public interface IOllamaProxyService
{
    /// <summary>
    /// Forwards a request to Ollama and returns the response.
    /// Use this for non-streaming endpoints.
    /// </summary>
    Task<HttpResponseMessage> ForwardRequestAsync(
        HttpRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Forwards a request to Ollama with streaming support.
    /// Use this for /api/chat, /api/generate, /api/embed, /api/embeddings endpoints.
    /// </summary>
    Task ForwardStreamingRequestAsync(
        HttpRequest request,
        HttpResponse response,
        CancellationToken cancellationToken = default);
}
