using EmbeddingGateway.Services;
using Microsoft.AspNetCore.Mvc;

namespace EmbeddingGateway.Endpoints;

/// <summary>
/// Endpoint mappings for Ollama proxy service.
/// Routes /api/ollama/{**path} to Ollama service.
/// </summary>
public static class OllamaEndpoints
{
    /// <summary>
    /// Maps Ollama proxy endpoints.
    /// </summary>
    public static IEndpointRouteBuilder MapOllamaProxyEndpoints(this IEndpointRouteBuilder endpoints)
    {
        // Streaming endpoints: /api/chat, /api/generate, /api/embed, /api/embeddings
        endpoints.Map("/api/ollama/api/{**path}", HandleStreamingRequest);
        endpoints.Map("/api/ollama/api/chat", HandleStreamingRequest);
        endpoints.Map("/api/ollama/api/generate", HandleStreamingRequest);
        endpoints.Map("/api/ollama/api/embed", HandleStreamingRequest);
        endpoints.Map("/api/ollama/api/embeddings", HandleStreamingRequest);
        
        // Non-streaming endpoints (fallback)
        endpoints.Map("/api/ollama/{**path}", HandleNonStreamingRequest);

        return endpoints;
    }

    private static async Task HandleStreamingRequest(
        HttpContext context,
        IOllamaProxyService proxyService)
    {
        try
        {
            await proxyService.ForwardStreamingRequestAsync(
                context.Request,
                context.Response,
                context.RequestAborted);
        }
        catch (OperationCanceledException)
        {
            // Client disconnected, ignore
        }
        catch (Exception ex)
        {
            context.Response.StatusCode = StatusCodes.Status502BadGateway;
            await context.Response.WriteAsJsonAsync(new
            {
                error = "Failed to proxy request to Ollama",
                details = ex.Message
            });
        }
    }

    private static async Task HandleNonStreamingRequest(
        HttpContext context,
        IOllamaProxyService proxyService)
    {
        try
        {
            using var response = await proxyService.ForwardRequestAsync(
                context.Request,
                context.RequestAborted);

            context.Response.StatusCode = (int)response.StatusCode;

            // Copy response headers
            foreach (var header in response.Headers)
            {
                context.Response.Headers[header.Key] = header.Value.ToArray();
            }

            foreach (var header in response.Content.Headers)
            {
                context.Response.Headers[header.Key] = header.Value.ToArray();
            }

            await response.Content.CopyToAsync(context.Response.Body, context.RequestAborted);
        }
        catch (OperationCanceledException)
        {
            // Client disconnected, ignore
        }
        catch (Exception ex)
        {
            context.Response.StatusCode = StatusCodes.Status502BadGateway;
            await context.Response.WriteAsJsonAsync(new
            {
                error = "Failed to proxy request to Ollama",
                details = ex.Message
            });
        }
    }
}
