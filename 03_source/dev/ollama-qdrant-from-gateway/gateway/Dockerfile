FROM mcr.microsoft.com/dotnet/aspnet:8.0-alpine AS runtime
WORKDIR /app
EXPOSE 11435
COPY src/EmbeddingGateway/bin/Release/net8.0/publish/ .
ENTRYPOINT ["dotnet", "EmbeddingGateway.dll"]

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY src/EmbeddingGateway/EmbeddingGateway.csproj ./
RUN dotnet restore
COPY src/EmbeddingGateway/ ./
RUN dotnet publish -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:8.0-alpine AS final
WORKDIR /app
COPY --from=build /app/publish .
EXPOSE 11435
ENV ASPNETCORE_URLS=http://+:11435
ENTRYPOINT ["dotnet", "EmbeddingGateway.dll"]
