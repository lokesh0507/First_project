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





// ✅ API in Service-A that calls Service-G using GET
app.MapGet("/call-g", async (IHttpClientFactory factory) =>
{
    var client = factory.CreateClient();

    var response = await client.GetFromJsonAsync<object>(
        "http://localhost:5500/get-from-g"  // Service-G URL
    );

    return Results.Ok(response);
});







app.Run();