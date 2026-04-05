FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy csproj and restore dependencies
COPY ["src/EmbeddingGateway/EmbeddingGateway.csproj", "src/EmbeddingGateway/"]
RUN dotnet restore "src/EmbeddingGateway/EmbeddingGateway.csproj"

# Copy everything else and build
COPY ["src/EmbeddingGateway/", "src/EmbeddingGateway/"]
WORKDIR "/src/src/EmbeddingGateway"
RUN dotnet build "EmbeddingGateway.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "EmbeddingGateway.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:8.0-alpine AS final
WORKDIR /app
EXPOSE 8080

# Copy the published output from the build stage
COPY --from=publish /app/publish .

# Set environment variables for configuration
ENV ASPNETCORE_URLS=http://+:8080
ENV UpstreamServices__Ollama=http://ollama:11434
ENV UpstreamServices__Qdrant=http://qdrant:6333

ENTRYPOINT ["dotnet", "EmbeddingGateway.dll"]
