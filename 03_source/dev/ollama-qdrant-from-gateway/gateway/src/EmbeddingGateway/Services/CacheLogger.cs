using System.Text.Json;

namespace EmbeddingGateway.Services;

/// <summary>
/// Cache logging service for RAG Gateway.
/// Provides structured logging for cache hits, misses, and coalesced requests.
/// Supports text and JSON output formats.
/// </summary>
public static class CacheLogger
{
    private static volatile bool _useJson = false;

    /// <summary>
    /// Configures the output format for cache logs.
    /// </summary>
    /// <param name="useJson">If true, outputs JSON format; otherwise, outputs human-readable text format.</param>
    public static void Configure(bool useJson)
    {
        _useJson = useJson;
    }

    /// <summary>
    /// Logs a cache hit event.
    /// </summary>
    /// <param name="key">Cache key (e.g., "emb:a3f5...").</param>
    /// <param name="size">Size of the cached data in bytes.</param>
    /// <exception cref="ArgumentNullException">Thrown when key is null.</exception>
    /// <exception cref="ArgumentOutOfRangeException">Thrown when size is negative.</exception>
    public static void Hit(string key, int size)
    {
        ValidateArguments(key, size);
        Log("CACHE_HIT", key, size, null);
    }

    /// <summary>
    /// Logs a cache miss event with inference duration.
    /// </summary>
    /// <param name="key">Cache key (e.g., "emb:a3f5...").</param>
    /// <param name="size">Size of the request body in bytes.</param>
    /// <param name="durationSeconds">Time taken for inference in seconds.</param>
    /// <exception cref="ArgumentNullException">Thrown when key is null.</exception>
    /// <exception cref="ArgumentOutOfRangeException">Thrown when size or durationSeconds is negative.</exception>
    public static void Miss(string key, int size, double durationSeconds)
    {
        ValidateArguments(key, size);
        if (durationSeconds < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(durationSeconds), "Duration cannot be negative.");
        }
        Log("CACHE_MISS", key, size, durationSeconds);
    }

    /// <summary>
    /// Logs a coalesced request event (client waited for another in-flight request).
    /// </summary>
    /// <param name="key">Cache key (e.g., "emb:a3f5...").</param>
    /// <exception cref="ArgumentNullException">Thrown when key is null.</exception>
    public static void Coalesced(string key)
    {
        if (key == null)
        {
            throw new ArgumentNullException(nameof(key), "Cache key cannot be null.");
        }
        Log("CACHE_COALESCED", key, 0, null);
    }

    private static void ValidateArguments(string key, int size)
    {
        if (key == null)
        {
            throw new ArgumentNullException(nameof(key), "Cache key cannot be null.");
        }
        if (size < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(size), "Size cannot be negative.");
        }
    }

    private static void Log(string @event, string key, int size, double? durationSeconds)
    {
        var timestamp = DateTime.UtcNow;

        if (_useJson)
        {
            // JSON format for Loki/ELK/Prometheus
            var entry = new
            {
                ts = timestamp.ToString("O"),
                @event,
                key,
                size,
                duration = durationSeconds
            };
            Console.WriteLine(JsonSerializer.Serialize(entry));
        }
        else
        {
            // Human-readable text format for debugging
            var durationStr = durationSeconds.HasValue ? $" | {durationSeconds.Value:F1}s" : "";
            var sizeStr = FormatSize(size);
            Console.WriteLine($"[{@event}] {key} | {sizeStr}{durationStr} | {timestamp:HH:mm:ss.fff}");
        }
    }

    private static string FormatSize(int bytes)
    {
        if (bytes >= 1024 * 1024)
        {
            return $"{bytes / (1024.0 * 1024.0):F1}MB";
        }
        if (bytes >= 1024)
        {
            return $"{bytes / 1024.0:F1}KB";
        }
        return $"{bytes}B";
    }
}
