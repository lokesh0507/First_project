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

app.MapGet("/call-a", () => "Service A is running");   

app.MapGet("/call-b", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();
    var response = await client.GetAsync("http://localhost:5125/items");
    var body = await response.Content.ReadAsStringAsync();
    return Results.Ok($"Service-A called Service-B. Response: {body}");
});

app.MapGet("/call-a", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();
    var response = await client.GetAsync("http://localhost:5000/call-a");
    var body = await response.Content.ReadAsStringAsync();

    return Results.Ok($"Service-D called Service-A → {body}");
});


app.Run();