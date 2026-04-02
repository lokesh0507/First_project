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

// ✅ POST endpoint to receive data from Service-B
app.MapPost("/receive-from-b", (ServiceBPayload data) =>
{
    return Results.Ok(new
    {
        Message = "Service C received data from Service B",
        Data = data
    });
});

// ✅ NEW: POST endpoint to receive data
// app.MapPost("/receive-data", (ServiceDPayload data) =>
// {
//     return Results.Ok(new
//     {
//         Message = "Service C received POST data",
//         Received = data
//     });
// });


// ✅ Service-B → POST data to Service-C
// app.MapPost("/post-to-service-c", async (IHttpClientFactory factory) =>
// {
//     var client = factory.CreateClient();

//     var payload = new
//     {
//         Name = "Item from Service B",
//         Quantity = 25

// };

//     var response = await client.PostAsJsonAsync(
//         "http://localhost:5200/receive-from-b",
//         payload
//     );

//     var result = await response.Content.ReadAsStringAsync();
//     return Results.Ok($"Service B posted data to Service C → {result}");
// });




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

app.Run();
