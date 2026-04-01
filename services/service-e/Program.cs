var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/health", () =>
{
    return Results.Ok("Service E is alive");
});

app.MapGet("/call-service-c", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();
    var response = await client.GetAsync("http://localhost:5200/items");
    var body = await response.Content.ReadAsStringAsync();

    return Results.Ok($"Service-E called Service-C → {body}");
});


app.Run();
