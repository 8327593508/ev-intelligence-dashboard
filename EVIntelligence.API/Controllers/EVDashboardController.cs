using Microsoft.AspNetCore.Mvc;
using Npgsql;

namespace EVIntelligence.API.Controllers
{
    [ApiController]
    [Route("api/dashboard")]
    public class EVDashboardController : ControllerBase
    {
        private readonly string _conn;

        public EVDashboardController(IConfiguration config)
        {
            _conn = config.GetConnectionString("DefaultConnection");
        }

        // ================= KPI ENDPOINT =================
        [HttpGet("kpis")]
        public IActionResult GetKPIs()
        {
            using var conn = new NpgsqlConnection(_conn);
            conn.Open();

            var totalEV = new NpgsqlCommand(
                "SELECT COALESCE(SUM(total_ev_registrations),0) FROM ev_india_monthly",
                conn
            ).ExecuteScalar();

            var chargers = new NpgsqlCommand(
                "SELECT COUNT(*) FROM charging_stations",
                conn
            ).ExecuteScalar();

            var forecast = new NpgsqlCommand(
                "SELECT predicted_ev_registrations FROM ev_forecast ORDER BY date DESC LIMIT 1",
                conn
            ).ExecuteScalar();

            var states = new NpgsqlCommand(
                "SELECT COUNT(*) FROM state_ev_adoption",
                conn
            ).ExecuteScalar();

            return Ok(new
            {
                totalEV,
                totalChargers = chargers,
                nextForecast = forecast,
                activeStates = states
            });
        }

        // ================= EV TREND (OVERVIEW) =================
        [HttpGet("ev-trend")]
        public IActionResult EVTrend()
        {
            using var conn = new NpgsqlConnection(_conn);
            conn.Open();

            var dates = new List<string>();
            var historical = new List<decimal>();

            var cmd = new NpgsqlCommand(
                "SELECT date, total_ev_registrations FROM ev_india_monthly ORDER BY date",
                conn
            );

            using (var reader = cmd.ExecuteReader())
            {
                while (reader.Read())
                {
                    dates.Add(reader.GetDateTime(0).ToString("yyyy-MM"));
                    historical.Add(reader.GetDecimal(1));
                }
            }

            var forecast = new List<decimal>();
            var cmd2 = new NpgsqlCommand(
                "SELECT predicted_ev_registrations FROM ev_forecast ORDER BY date",
                conn
            );

            using (var r2 = cmd2.ExecuteReader())
            {
                while (r2.Read())
                {
                    forecast.Add(r2.GetDecimal(0));
                }
            }

            return Ok(new { dates, historical, forecast });
        }

        // ================= MONTHLY DATA =================
        [HttpGet("monthly")]
        public IActionResult Monthly()
        {
            using var conn = new NpgsqlConnection(_conn);
            conn.Open();

            var dates = new List<string>();
            var values = new List<decimal>();

            var cmd = new NpgsqlCommand(
                "SELECT date, total_ev_registrations FROM ev_india_monthly ORDER BY date DESC LIMIT 12",
                conn
            );

            using (var reader = cmd.ExecuteReader())
            {
                while (reader.Read())
                {
                    dates.Add(reader.GetDateTime(0).ToString("yyyy-MM"));
                    values.Add(reader.GetDecimal(1));
                }
            }

            return Ok(new { dates, values });
        }

        // ================= STATE ADOPTION =================
        [HttpGet("state-adoption")]
        public IActionResult StateAdoption()
        {
            using var conn = new NpgsqlConnection(_conn);
            conn.Open();

            var states = new List<string>();
            var values = new List<decimal>();

            var cmd = new NpgsqlCommand(
                "SELECT state, total_ev FROM state_ev_adoption ORDER BY total_ev DESC LIMIT 15",
                conn
            );

            using (var reader = cmd.ExecuteReader())
            {
                while (reader.Read())
                {
                    states.Add(reader.GetString(0));
                    values.Add(reader.GetDecimal(1));
                }
            }

            return Ok(new { states, values });
        }

        // ================= EV VS CHARGERS =================
        [HttpGet("ev-vs-chargers")]
        public IActionResult EVvsChargers()
        {
            using var conn = new NpgsqlConnection(_conn);
            conn.Open();

            var states = new List<string>();
            var ev = new List<decimal>();
            var chargers = new List<long>();

            var cmd = new NpgsqlCommand(@"
                SELECT a.state, a.total_ev, c.total_chargers
                FROM state_ev_adoption a
                JOIN state_chargers c ON a.state = c.state
                ORDER BY a.total_ev DESC
                LIMIT 10", conn);

            using (var reader = cmd.ExecuteReader())
            {
                while (reader.Read())
                {
                    states.Add(reader.GetString(0));
                    ev.Add(reader.GetDecimal(1));
                    chargers.Add(reader.GetInt64(2));
                }
            }

            return Ok(new { states, ev, chargers });
        }

        // ================= SCATTER (PRICE VS RANGE) =================
        [HttpGet("scatter")]
        public IActionResult Scatter()
        {
            using var conn = new NpgsqlConnection(_conn);
            conn.Open();

            var points = new List<object>();

            var cmd = new NpgsqlCommand(@"
                SELECT price, range_km 
                FROM ev_vehicle_specs 
                WHERE price IS NOT NULL 
                  AND range_km IS NOT NULL 
                LIMIT 50", conn);

            using (var reader = cmd.ExecuteReader())
            {
                while (reader.Read())
                {
                    points.Add(new
                    {
                        x = reader.GetDouble(0),
                        y = reader.GetDouble(1)
                    });
                }
            }

            return Ok(new { points });
        }

        // ================= MANUFACTURER SALES (ANALYTICS PAGE) =================
        [HttpGet("manufacturer-sales")]
        public IActionResult ManufacturerSales()
        {
            using var conn = new NpgsqlConnection(_conn);
            conn.Open();

            var labels = new List<string>();
            var values = new List<int>();

            var cmd = new NpgsqlCommand(@"
                SELECT m.manufacturer_name, SUM(ms.sales) AS total_sales
                FROM manufacturer_yearly_sales ms
                JOIN manufacturers m 
                    ON ms.manufacturer_id = m.manufacturer_id
                GROUP BY m.manufacturer_name
                ORDER BY total_sales DESC
                LIMIT 10", conn);

            using (var reader = cmd.ExecuteReader())
            {
                while (reader.Read())
                {
                    labels.Add(reader.GetString(0));
                    values.Add(reader.GetInt32(1));
                }
            }

            return Ok(new { labels, values });
        }

        // ================= CHARGERS BY STATE (INFRASTRUCTURE PAGE) =================
        [HttpGet("chargers-by-state")]
        public IActionResult ChargersByState()
        {
            using var conn = new NpgsqlConnection(_conn);
            conn.Open();

            var states = new List<string>();
            var values = new List<long>();

            var cmd = new NpgsqlCommand(@"
                SELECT state, total_chargers
                FROM state_chargers
                ORDER BY total_chargers DESC
                LIMIT 15", conn);

            using (var reader = cmd.ExecuteReader())
            {
                while (reader.Read())
                {
                    states.Add(reader.GetString(0));
                    values.Add(reader.GetInt64(1));
                }
            }

            return Ok(new { states, values });
        }

        [HttpGet("vehicle-types")]
public IActionResult VehicleTypes()
{
    using var conn = new NpgsqlConnection(_conn);
    conn.Open();

    var labels = new List<string>();
    var values = new List<int>();

    var cmd = new NpgsqlCommand(@"
        SELECT vt.type_name, SUM(er.registration_count) AS total
        FROM ev_registrations er
        JOIN vehicle_types vt 
            ON er.vehicle_type_id = vt.vehicle_type_id
        GROUP BY vt.type_name
        ORDER BY total DESC
    ", conn);

    using var reader = cmd.ExecuteReader();
    while (reader.Read())
    {
        labels.Add(reader.GetString(0));
        values.Add(Convert.ToInt32(reader.GetInt64(1)));
    }

    return Ok(new { labels, values });
}

[HttpGet("power-connectors")]
public IActionResult PowerConnectors()
{
    using var conn = new NpgsqlConnection(_conn);
    conn.Open();

    var points = new List<object>();

    var cmd = new NpgsqlCommand(@"
        SELECT power_kw, num_connectors
        FROM charging_stations
        WHERE power_kw IS NOT NULL 
        AND num_connectors IS NOT NULL
        LIMIT 50", conn);

    using var reader = cmd.ExecuteReader();
    while (reader.Read())
    {
        points.Add(new
        {
            x = reader.GetDouble(0), // power_kw
            y = reader.GetInt32(1),  // connectors
            r = 5 + (reader.GetInt32(1) / 2) // bubble size
        });
    }

    return Ok(new { points });
}

// ================= INFRASTRUCTURE: PRICE VS RANGE (REUSE VEHICLE TABLE) =================
[HttpGet("infra-price-range")]
public IActionResult InfraPriceRange()
{
    using var conn = new NpgsqlConnection(_conn);
    conn.Open();

    var points = new List<object>();

    var cmd = new NpgsqlCommand(@"
        SELECT price, range_km
        FROM ev_vehicle_specs
        WHERE price IS NOT NULL 
          AND range_km IS NOT NULL
        LIMIT 50", conn);

    using var reader = cmd.ExecuteReader();
    while (reader.Read())
    {
        points.Add(new
        {
            x = reader.GetDouble(0), // price
            y = reader.GetDouble(1)  // range
        });
    }

    return Ok(new { points });
}

// ================= INFRASTRUCTURE: BATTERY VS RANGE RADAR =================
[HttpGet("infra-battery-radar")]
public IActionResult InfraBatteryRadar()
{
    using var conn = new NpgsqlConnection(_conn);
    conn.Open();

    var labels = new List<string>();
    var values = new List<double>();

    var cmd = new NpgsqlCommand(@"
        SELECT model_name, range_km
        FROM ev_vehicle_specs
        WHERE range_km IS NOT NULL
        ORDER BY range_km DESC
        LIMIT 6", conn);

    using var reader = cmd.ExecuteReader();
    while (reader.Read())
    {
        labels.Add(reader.GetString(0));
        values.Add(reader.GetDouble(1));
    }

    return Ok(new { labels, values });
}

// ================= INFRASTRUCTURE: CHARGER LEVEL DISTRIBUTION =================
[HttpGet("infra-charger-level")]
public IActionResult InfraChargerLevel()
{
    using var conn = new NpgsqlConnection(_conn);
    conn.Open();

    var labels = new List<string>();
    var values = new List<int>();

    var cmd = new NpgsqlCommand(@"
        SELECT charger_level, COUNT(*) 
        FROM charging_stations
        WHERE charger_level IS NOT NULL
        GROUP BY charger_level
        ORDER BY COUNT(*) DESC", conn);

    using var reader = cmd.ExecuteReader();
    while (reader.Read())
    {
        labels.Add(reader.GetString(0));
        values.Add(reader.GetInt32(1));
    }

    return Ok(new { labels, values });
}


    }
}