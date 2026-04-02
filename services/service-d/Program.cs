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

// ✅ NEW: POST from service-d → service-c
app.MapPost("/post-to-service-c", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();

    var payload = new
    {
        Message = "Hello from Service D",
        Count = 10
    };

    var response = await client.PostAsJsonAsync(
        "http://localhost:5200/receive-data",
        payload

 );

    var result = await response.Content.ReadAsStringAsync();
    return Results.Ok($"Service-D posted data → {result}");
});



app.Run();
