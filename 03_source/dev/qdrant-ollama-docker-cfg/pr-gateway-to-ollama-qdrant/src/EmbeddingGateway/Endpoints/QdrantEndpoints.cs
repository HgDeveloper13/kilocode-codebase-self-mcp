using EmbeddingGateway.Services;

namespace EmbeddingGateway.Endpoints;

/// <summary>
/// Endpoint mappings for Qdrant proxy service.
/// Routes /api/qdrant/{**path} to Qdrant service.
/// </summary>
public static class QdrantEndpoints
{
    /// <summary>
    /// Maps Qdrant proxy endpoints.
    /// </summary>
    public static IEndpointRouteBuilder MapQdrantProxyEndpoints(this IEndpointRouteBuilder endpoints)
    {
        endpoints.Map("/api/qdrant/{**path}", HandleRequest);

        return endpoints;
    }

    private static async Task HandleRequest(
        HttpContext context,
        IQdrantProxyService proxyService)
    {
        try
        {
            await proxyService.ForwardRequestAsync(
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
                error = "Failed to proxy request to Qdrant",
                details = ex.Message
            });
        }
    }
}
