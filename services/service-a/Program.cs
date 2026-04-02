using Confluent.Kafka;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddHttpClient();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// ------------------- EXISTING REST ENDPOINTS -------------------

app.MapGet("/call-a", () => "Service A is running");

app.MapGet("/call-b", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();
    var response = await client.GetAsync("http://localhost:5125/items");
    var body = await response.Content.ReadAsStringAsync();
    return Results.Ok($"Service-A called Service-B. Response: {body}");
});

app.MapGet("/call-service-c", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();
    var response = await client.GetAsync("http://localhost:5200/items");
    return Results.Ok(await response.Content.ReadAsStringAsync());
});

app.MapGet("/call-e", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();
    var response = await client.GetAsync("http://localhost:5292/health");
    return Results.Ok(await response.Content.ReadAsStringAsync());
});

// ------------------- ✅ KAFKA PRODUCER (NEW) -------------------

// Kafka producer configuration
var producerConfig = new ProducerConfig
{
    BootstrapServers = "localhost:9092"
};

var producer = new ProducerBuilder<Null, string>(producerConfig).Build();

// ✅ New endpoint: Service-A → Kafka
app.MapGet("/publish-order", async () =>
{
    var message = $"Order created by Service-A at {DateTime.Now}";

    await producer.ProduceAsync(
        "orders-topic",
        new Message<Null, string> { Value = message }
    );

    return Results.Ok($"Message published to Kafka: {message}");
});

app.Run();
