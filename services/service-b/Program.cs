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

// ✅ Replaces POST to service-c
app.MapPost("/publish-order", async () =>
{
    using var producer =
        new ProducerBuilder<Null, string>(producerConfig).Build();

    var orderEvent = new
    {
        OrderId = Guid.NewGuid().ToString(),
        CreatedBy = "service-b",
        CreatedAt = DateTime.UtcNow
    };

    var message = new Message<Null, string>
    {
        Value = JsonSerializer.Serialize(orderEvent)
    };

    await producer.ProduceAsync("order-created", message);

    return Results.Ok("✅ Order event published to Kafka");
});


 
app.Run();