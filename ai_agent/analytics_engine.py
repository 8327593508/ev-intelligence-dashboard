import re
from typing import Dict, Any, Optional, List


# =====================================================
# 🔹 GLOBAL NORMALIZER (CASE INSENSITIVE ENGINE)
# =====================================================
def normalize(text: str) -> str:
    return text.lower().strip()


# =====================================================
# 🔹 STATE EXTRACTION (CASE INSENSITIVE)
# =====================================================
def extract_state(question: str) -> Optional[str]:

    states = [
        "andhra pradesh","arunachal pradesh","assam","bihar",
        "chhattisgarh","goa","gujarat","haryana","himachal pradesh",
        "jharkhand","karnataka","kerala","madhya pradesh",
        "maharashtra","manipur","meghalaya","mizoram",
        "nagaland","odisha","punjab","rajasthan",
        "sikkim","tamil nadu","telangana","tripura",
        "uttar pradesh","uttarakhand","west bengal","delhi"
    ]

    q = normalize(question)

    for state in states:
        if state in q:
            return state.title()

    return None


# =====================================================
# 🔹 RESPONSE BUILDER
# =====================================================
def build_response(
    sql: str,
    summary: str,
    chart_type: Optional[str] = None
) -> Dict[str, Any]:

    return {
        "sql": sql.strip(),
        "summary": summary,
        "chart_type": chart_type
    }


# =====================================================
# 🔹 TOP / LOWEST STATES
# =====================================================
def detect_top_states(question: str) -> Optional[Dict[str, Any]]:

    q = normalize(question)

    if "state" in q and any(word in q for word in ["top","highest","lowest"]):

        limit_match = re.search(r"(top|highest|lowest)\s+(\d+)", q)
        limit = int(limit_match.group(2)) if limit_match else 5

        order = "DESC"
        context = "highest"
        if "lowest" in q:
            order = "ASC"
            context = "lowest"

        sql = f"""
        SELECT state,
               SUM(estimated_ev_registrations) AS total_registrations
        FROM ev_registrations_state_weighted
        WHERE state NOT IN ('India','Grand Total','Total','Unknown','')
        GROUP BY state
        ORDER BY total_registrations {order}
        LIMIT {limit}
        """

        summary = f"Here are the top {limit} states with {context} EV registrations based on weighted analytics."

        return build_response(sql, summary, "bar")

    return None


# =====================================================
# 🔹 TOTAL EV (NATIONAL)
# =====================================================
def detect_total_ev(question: str) -> Optional[Dict[str, Any]]:

    q = normalize(question)

    if "total ev" in q and "state" not in q:

        sql = """
        SELECT SUM(estimated_ev_registrations) AS total_registrations
        FROM ev_registrations_state_weighted
        WHERE state NOT IN ('India','Grand Total','Total','Unknown','')
        """

        summary = "Here is the total estimated EV registrations across all states."

        return build_response(sql, summary)

    return None


# =====================================================
# 🔹 VEHICLE TYPE SALES ANALYSIS
# =====================================================
def detect_vehicle_sales_by_type(question: str) -> Optional[Dict[str, Any]]:

    q = normalize(question)

    if "sales" in q and "type" in q:

        sql = """
        SELECT vt.type_name,
               SUM(ms.sales) AS total_sales
        FROM manufacturer_yearly_sales ms
        JOIN vehicle_types vt
            ON ms.vehicle_type_id = vt.vehicle_type_id
        GROUP BY vt.type_name
        ORDER BY total_sales DESC
        """

        summary = "Here is the total vehicle sales aggregated by vehicle type."

        return build_response(sql, summary, "bar")

    return None


# =====================================================
# 🔹 VEHICLE SPEC ANALYTICS
# =====================================================
def detect_vehicle_specs(question: str) -> Optional[Dict[str, Any]]:

    q = normalize(question)

    # Average Range
    if "average" in q and "range" in q:

        sql = """
        SELECT vt.type_name,
               AVG(vs.range_km) AS avg_range_km
        FROM ev_vehicle_specs vs
        JOIN vehicle_types vt
            ON vs.vehicle_type_id = vt.vehicle_type_id
        GROUP BY vt.type_name
        ORDER BY avg_range_km DESC
        """

        summary = "Here is the average driving range (km) by vehicle type."

        return build_response(sql, summary, "bar")

    # Average Charging Time
    if "average" in q and "charging" in q:

        sql = """
        SELECT vt.type_name,
               AVG(vs.charging_time_hr) AS avg_charging_time_hr
        FROM ev_vehicle_specs vs
        JOIN vehicle_types vt
            ON vs.vehicle_type_id = vt.vehicle_type_id
        GROUP BY vt.type_name
        ORDER BY avg_charging_time_hr
        """

        summary = "Here is the average charging time (hours) by vehicle type."

        return build_response(sql, summary, "bar")

    # Average Battery
    if "average" in q and "battery" in q:

        sql = """
        SELECT vt.type_name,
               AVG(vs.battery_capacity_kwh) AS avg_battery_capacity
        FROM ev_vehicle_specs vs
        JOIN vehicle_types vt
            ON vs.vehicle_type_id = vt.vehicle_type_id
        GROUP BY vt.type_name
        ORDER BY avg_battery_capacity DESC
        """

        summary = "Here is the average battery capacity (kWh) by vehicle type."

        return build_response(sql, summary, "bar")

    # Average Price
    if "average" in q and "price" in q:

        sql = """
        SELECT vt.type_name,
               AVG(vs.price) AS avg_price
        FROM ev_vehicle_specs vs
        JOIN vehicle_types vt
            ON vs.vehicle_type_id = vt.vehicle_type_id
        GROUP BY vt.type_name
        ORDER BY avg_price DESC
        """

        summary = "Here is the average vehicle price by type."

        return build_response(sql, summary, "bar")

    return None


# =====================================================
# 🔹 CHARGER ANALYSIS
# =====================================================
def detect_charger_analysis(question: str) -> Optional[Dict[str, Any]]:

    q = normalize(question)

    if "charger" in q or "charging" in q:

        if "operator" in q:

            sql = """
            SELECT operator,
                   COUNT(*) AS total_stations
            FROM charging_stations
            GROUP BY operator
            ORDER BY total_stations DESC
            LIMIT 10
            """

            summary = "Here are the top charging station operators by total stations."

            return build_response(sql, summary, "bar")

        if "state" in q:

            sql = """
            SELECT state,
                   total_chargers
            FROM state_chargers
            ORDER BY total_chargers DESC
            LIMIT 10
            """

            summary = "Here are the top states ranked by charging infrastructure."

            return build_response(sql, summary, "bar")

        sql = """
        SELECT SUM(total_chargers) AS total_chargers
        FROM state_chargers
        """

        summary = "Here is the total number of EV charging stations nationwide."

        return build_response(sql, summary)

    return None


# =====================================================
# 🔹 FORECAST
# =====================================================
def detect_forecast(question: str) -> Optional[Dict[str, Any]]:

    q = normalize(question)

    if "forecast" in q:

        sql = """
        SELECT date,
               predicted_ev_registrations
        FROM ev_forecast
        ORDER BY date
        """

        summary = "Here is the EV registration forecast trend over time."

        return build_response(sql, summary, "line")

    return None


def detect_cagr(question: str):

    q = normalize(question)
    years = re.findall(r"\b(20\d{2})\b", q)

    if ("cagr" in q or "growth rate" in q) and len(years) >= 2:

        # Sort years safely
        start_year, end_year = sorted(map(int, years[:2]))

        # Prevent invalid range
        if end_year <= start_year:
            return None

        sql = f"""
        WITH yearly_data AS (
            SELECT year,
                   SUM(estimated_ev_registrations) AS total
            FROM ev_registrations_state_weighted
            WHERE year IN ({start_year}, {end_year})
              AND state NOT IN ('India','Grand Total','Total','Unknown','')
            GROUP BY year
        )
        SELECT
            MIN(CASE WHEN year = {start_year} THEN total END) AS start_value,
            MIN(CASE WHEN year = {end_year} THEN total END) AS end_value,
            {end_year - start_year} AS num_years
        FROM yearly_data
        """

        summary = f"Computing CAGR from {start_year} to {end_year}."

        return build_response(sql, summary)

    return None


def detect_yoy_growth(question: str):

    q = normalize(question)
    years = re.findall(r"\b(20\d{2})\b", q)

    if "growth" in q and len(years) >= 2:

        y1, y2 = years[:2]

        sql = f"""
        SELECT year,
               SUM(estimated_ev_registrations) AS total
        FROM ev_registrations_state_weighted
        WHERE year IN ({y1}, {y2})
        AND state NOT IN ('India','Grand Total','Total','Unknown','')
        GROUP BY year
        ORDER BY year
        """

        summary = f"Comparing EV growth between {y1} and {y2}."

        return build_response(sql, summary, "line")

    return None


def detect_ev_to_charger_ratio(question: str):

    q = normalize(question)

    if "ratio" in q and "charger" in q:

        sql = """
        SELECT
            ev.state,
            SUM(ev.estimated_ev_registrations) /
            NULLIF(sc.total_chargers, 0) AS ev_to_charger_ratio
        FROM ev_registrations_state_weighted ev
        JOIN state_chargers sc
            ON ev.state = sc.state
        WHERE ev.state NOT IN ('India','Grand Total','Total','Unknown','')
        GROUP BY ev.state, sc.total_chargers
        ORDER BY ev_to_charger_ratio DESC
        """

        summary = "Here is the EV to charger ratio by state."

        return build_response(sql, summary, "bar")

    return None


def detect_market_share(question: str):

    q = normalize(question)

    if "market share" in q:

        sql = """
        WITH total_sales AS (
            SELECT SUM(sales) AS grand_total
            FROM manufacturer_yearly_sales
        )
        SELECT
            m.manufacturer_name,
            SUM(ms.sales) AS total_sales,
            (SUM(ms.sales) * 100.0 /
             (SELECT grand_total FROM total_sales)) AS market_share_percentage
        FROM manufacturer_yearly_sales ms
        JOIN manufacturers m
            ON ms.manufacturer_id = m.manufacturer_id
        GROUP BY m.manufacturer_name
        ORDER BY total_sales DESC
        """

        summary = "Here is the market share percentage by manufacturer."

        return build_response(sql, summary, "bar")

    return None


def detect_moving_average(question: str):

    q = normalize(question)

    if "moving average" in q:

        sql = """
        SELECT date,
               AVG(total_ev_registrations)
               OVER (ORDER BY date
                     ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
               AS moving_avg
        FROM ev_india_monthly
        ORDER BY date
        """

        summary = "Here is the 3-month moving average of EV registrations."

        return build_response(sql, summary, "line")

    return None


# =====================================================
# 🔹 MASTER ROUTER
# =====================================================
def try_advanced_analytics(question: str) -> Optional[Dict[str, Any]]:

    detectors = [
        detect_top_states,
        detect_total_ev,
        detect_vehicle_sales_by_type,
        detect_vehicle_specs,
        detect_charger_analysis,
        detect_forecast,
        detect_cagr,
        detect_yoy_growth,
        detect_ev_to_charger_ratio,
        detect_market_share,
    detect_moving_average
    ]

    for detector in detectors:
        result = detector(question)
        if result:
            return result

    return None