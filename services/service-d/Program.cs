var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient();

var app = builder.Build();

app.MapGet("/", () => "Service-D is running");

// ✅ Service‑D calling Service‑A
app.MapGet("/call-service-a", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();
    var response = await client.GetAsync("http://localhost:5000/call-a");
    var body = await response.Content.ReadAsStringAsync();

    return Results.Ok($"Service-D called Service-A → {body}");
});

app.MapGet("/call-service-c", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();
    var response = await client.GetAsync("http://localhost:5200/items");
    var body = await response.Content.ReadAsStringAsync();

    return Results.Ok($"Service-D called Service-C → {body}");
});


app.Run();
