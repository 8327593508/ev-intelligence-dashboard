using Microsoft.AspNetCore.Mvc;
using System.Text;
using System.Text.Json;

namespace EVIntelligence.API.Controllers
{
    [ApiController]
    [Route("api/ai")]
    public class AIAgentController : ControllerBase
    {
        private readonly HttpClient _httpClient;

        public AIAgentController(IHttpClientFactory httpClientFactory)
        {
            _httpClient = httpClientFactory.CreateClient();
            _httpClient.Timeout = TimeSpan.FromSeconds(60);
        }

        // POST: api/ai/chat
        [HttpPost("chat")]
        public async Task<IActionResult> Chat([FromBody] AIRequest request)
        {
            try
            {
                if (request == null || string.IsNullOrWhiteSpace(request.Question))
                {
                    return Ok(new
                    {
                        answer = "Please enter a valid EV-related question.",
                        chart = (object)null,
                        data = new object[] { }
                    });
                }

                var payload = new
                {
                    question = request.Question
                };

                var content = new StringContent(
                    JsonSerializer.Serialize(payload),
                    Encoding.UTF8,
                    "application/json"
                );

                // 🔥 Call FastAPI Agent (Port 8001)
                var response = await _httpClient.PostAsync(
                    "http://127.0.0.1:8001/ask",
                    content
                );

                if (!response.IsSuccessStatusCode)
                {
                    return Ok(new
                    {
                        answer = "Moxie AI service responded with an error.",
                        chart = (object)null,
                        data = new object[] { }
                    });
                }

                var jsonString = await response.Content.ReadAsStringAsync();

                // 🔥 PARSE FULL JSON (ANSWER + CHART + DATA)
                using var jsonDoc = JsonDocument.Parse(jsonString);
                var root = jsonDoc.RootElement;

                string answer = root.TryGetProperty("answer", out var ansEl)
                    ? ansEl.GetString() ?? "No response generated."
                    : "No answer field found from AI service.";

                object chart = null;
                if (root.TryGetProperty("chart", out var chartEl) &&
                    chartEl.ValueKind != JsonValueKind.Null)
                {
                    chart = JsonSerializer.Deserialize<object>(chartEl.GetRawText());
                }

                object data = new object[] { };
                if (root.TryGetProperty("data", out var dataEl) &&
                    dataEl.ValueKind == JsonValueKind.Array)
                {
                    data = JsonSerializer.Deserialize<object>(dataEl.GetRawText());
                }

                // ✅ RETURN FULL STRUCTURED RESPONSE TO FRONTEND
                return Ok(new
                {
                    answer = answer,
                    chart = chart,
                    data = data
                });
            }
            catch (Exception ex)
            {
                return Ok(new
                {
                    answer = "Moxie AI is running, but the response could not be processed. Please try another EV-related query.",
                    chart = (object)null,
                    data = new object[] { }
                });
            }
        }
    }

    public class AIRequest
    {
        public string Question { get; set; } = string.Empty;
    }
}