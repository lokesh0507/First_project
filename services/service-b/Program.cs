var builder = WebApplication.CreateBuilder(args);
 
var app = builder.Build();
 
// Simple endpoint: returns dummy items
app.MapGet("/items", () =>
{
    return Results.Ok(new [] { "Schlage", "LCN", "Zentra" });
});

app.MapGet("/call-a", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();

    var response = await client.GetAsync("http://localhost:5000/health");
    return Results.Ok(await response.Content.ReadAsStringAsync());
});

 
app.Run();