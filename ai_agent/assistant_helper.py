import random

# =====================================================
# HELP PROMPTS LIBRARY
# =====================================================
HELP_PROMPTS = [

    # EV Registrations
    "Top 5 states with highest EV registrations",
    "Lowest 5 states by EV adoption",
    "Total EV registrations",
    "EV growth from 2020 to 2024",

    # Vehicle Type
    "Total sales vehicle type wise",
    "Average range type wise",
    "Average charging time by vehicle type",
    "Total 4W registered",

    # Infrastructure
    "Top states by charging infrastructure",
    "EV to charger ratio by state",

    # Forecast
    "Show EV forecast trend",
    "What is CAGR from 2020 to 2024?"
]


# =====================================================
# GENERAL RESPONSE TRACKER
# =====================================================
class ConversationManager:

    def __init__(self):
        self.general_response_count = 0

    def register_general_response(self):
        self.general_response_count += 1

    def reset_counter(self):
        self.general_response_count = 0

    def should_suggest_help(self):
        return self.general_response_count >= 2

    def generate_help_message(self):

        suggestions = random.sample(HELP_PROMPTS, 3)

        formatted = "\n\n".join([f"• {p}" for p in suggestions])

        return (
            "It looks like I couldn’t generate detailed EV insights.\n\n"
            "You can type 'help' to see example prompts.\n\n"
            "Here are some suggestions:\n\n"
            f"{formatted}"
        )

    def generate_help_only(self):

        suggestions = random.sample(HELP_PROMPTS, 3)

        formatted = "\n\n".join([f"• {p}" for p in suggestions])

        return (
            "Here are some example prompts you can try:\n\n"
            f"{formatted}"
        )