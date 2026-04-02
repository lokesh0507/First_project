using Confluent.Kafka;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);

// ✅ REQUIRED for HttpClient usage
builder.Services.AddHttpClient();

var app = builder.Build();

// ✅ Kafka producer configuration (MISSING in your code)
var producerConfig = new ProducerConfig
{
    BootstrapServers = "127.0.0.1:9092",
    ClientId = "service-b-producer"
};

// ✅ Simple endpoint: returns dummy items
app.MapGet("/items", () =>
{
    return Results.Ok(new[] { "Schlage", "LCN", "Zentra" });
});

// ✅ Service-B → GET calling Service-A
app.MapGet("/call-a", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();
    var response = await client.GetAsync("http://localhost:5000/health");
    return Results.Ok(await response.Content.ReadAsStringAsync());
});

// ✅ Kafka Producer: Service-B → Kafka → Service-D
app.MapPost("/publish-order", async () =>
{
    using var producer =
        new ProducerBuilder<Null, string>(producerConfig).Build();

    var orderEvent = new
    {
        OrderId = Guid.NewGuid().ToString(),
        CreatedBy = "service-b",
        TargetService = "service-d",
        CreatedAt = DateTime.UtcNow
    };

    var message = new Message<Null, string>
    {
        Value = JsonSerializer.Serialize(orderEvent)
    };

    await producer.ProduceAsync("order-created-bd", message);

    return Results.Ok("✅ Order event published to Kafka");
});
app.MapGet("/publish-order-browser", async () =>
{
    using var producer =
        new ProducerBuilder<Null, string>(producerConfig).Build();

    var orderEvent = new
    {
        OrderId = Guid.NewGuid().ToString(),
        CreatedBy = "service-b",
        TargetService = "service-d",
        TriggeredFrom = "browser",
        CreatedAt = DateTime.UtcNow
    };

    var message = new Message<Null, string>
    {
        Value = JsonSerializer.Serialize(orderEvent)
    };

    await producer.ProduceAsync("order-created-bd", message);

    return Results.Ok("✅ Kafka event triggered from browser");
});


app.Run();