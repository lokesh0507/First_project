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

// ✅ Check Service C is running
app.MapGet("/", () => "Service C is running");

// ✅ Service C → GET calling Service A (/call-a)
app.MapGet("/call-service-a", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();

    var response = await client.GetAsync("http://localhost:5000/call-a");
    var body = await response.Content.ReadAsStringAsync();

    return Results.Ok($"Service C called Service A. Response: {body}");
});




// ✅ Service C → POST data to Service A
app.MapPost("/post-to-a", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();

    var payload = new
    {
        Message = "Hello from Service C!",
        Timestamp = DateTime.Now
    };

    var result = await client.PostAsJsonAsync("http://localhost:5000/post-data", payload);
    var body = await result.Content.ReadAsStringAsync();

    return Results.Ok($"Service C posted data to A. Response: {body}");
});


// ------------------- ✅ KAFKA CONSUMER (NEW) -------------------

var consumerConfig = new ConsumerConfig
{
    BootstrapServers = "localhost:9092",
    GroupId = "service-c-group",
    AutoOffsetReset = AutoOffsetReset.Earliest
};

var consumer = new ConsumerBuilder<Ignore, string>(consumerConfig).Build();

Task.Run(() =>
{
    consumer.Subscribe("orders-topic");

    while (true)
    {
        try
        {
            var cr = consumer.Consume();
            Console.WriteLine($"[Service-C] Consumed message: {cr.Message.Value}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Kafka consume error: {ex.Message}");
        }
    }
});


app.Run();
