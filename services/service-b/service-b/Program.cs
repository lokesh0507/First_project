var builder = WebApplication.CreateBuilder(args);
 
var app = builder.Build();
 
// Simple endpoint: returns dummy items
app.MapGet("/items", () =>
{
    return Results.Ok(new [] { "Schlage", "LCN", "Zentra" });
});
 
app.Run();