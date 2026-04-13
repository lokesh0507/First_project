using Confluent.Kafka;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient();

var app = builder.Build();

// ✅ Health endpoint
app.MapGet("/", () => "Service-D is running");

// ✅ Service-D → GET calling Service-A
app.MapGet("/call-service-a", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();
    var response = await client.GetAsync("http://localhost:5000/call-a");
    var body = await response.Content.ReadAsStringAsync();
    return Results.Ok($"Service-D called Service-A → {body}");
});

// ✅ Service-D → GET calling Service-C
app.MapGet("/call-service-c", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();
    var response = await client.GetAsync("http://localhost:5200/addressdetails");
    var body = await response.Content.ReadAsStringAsync();
    return Results.Ok($"Service-D called Service-C → {body}");
});


// ===================================================
// ✅ Kafka Consumer (Service-B → Kafka → Service-D)
// ===================================================
Task.Run(() =>
{
    var config = new ConsumerConfig
    {
        BootstrapServers = "127.0.0.1:9092",
        GroupId = "service-d-group",
        AutoOffsetReset = AutoOffsetReset.Earliest
    };

    using var consumer =
        new ConsumerBuilder<Ignore, string>(config).Build();

    consumer.Subscribe("order-created-bd");

    Console.WriteLine("✅ Service-D Kafka consumer started and waiting for messages...");

    while (true)
    {
        try
        {
            var result = consumer.Consume();
            Console.WriteLine($"📥 Service-D consumed Kafka event → {result.Message.Value}");
        }
        catch (ConsumeException ex)
        {
            Console.WriteLine($"❌ Kafka consume error: {ex.Error.Reason}");
        }
    }
});

app.Run();