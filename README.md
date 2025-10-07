Google Ads Advanced Simulator
This is a comprehensive, full-featured simulation platform for Google Ads, designed to model, forecast, and analyze search campaign performance. It leverages a sophisticated backend to simulate ad auctions, apply advanced bidding strategies, and provide in-depth analytics, all within an interactive Streamlit web application.

The platform integrates directly with live Google Ads and Google AI APIs to pull real-world data for unparalleled accuracy in its simulations.

Key Features
Enhanced Campaign Wizard: A step-by-step guide to build detailed search campaigns, covering everything from objectives and budget to advanced targeting and ad extensions.

Realistic Ad Auction: A core simulation engine that models the Google Ads auction, incorporating Quality Score, Ad Rank, competitor bidding, and smart pricing.

Advanced Bidding Strategies: Implements multiple automated bidding strategies like Target CPA, Target ROAS, and Maximize Conversions, with an optional ML-based bidding model.

Real-time Budget Pacing: A pacing controller manages daily spend, adjusting bids throughout the day to ensure budgets are utilized effectively.

Live Keyword Planning: Integrates with the Google Ads API to fetch real keyword ideas, search volume, CPC data, and forecasts, with a fallback to mock data if the API is unavailable.

AI-Powered Ad Creation: Uses the Google Gemini API to automatically generate relevant keywords and compelling ad copy (headlines and descriptions) based on simple prompts.

Comprehensive Targeting: Apply layered targeting for Geographics, Devices, Audiences (Remarketing, In-Market, Affinity), Demographics, and Ad Scheduling (Dayparting).

Multi-Touch Attribution: Go beyond last-click attribution with models like Linear, Time Decay, and Position-Based to better understand the entire conversion path.

In-Depth Reporting: Visualize performance through a rich dashboard and detailed reports for campaigns, ad groups, keywords, search terms, and more.

AI Chat Assistant: An integrated Dialogflow chatbot provides contextual help and campaign optimization suggestions.

Project Structure
The project is organized into a modular structure for better maintainability and performance:

.
├── app/                  # Streamlit UI components
│   ├── components/         # Shared UI widgets (e.g., chatbot)
│   ├── pages/              # Individual app pages (Dashboard, Reports)
│   └── wizards/            # Multi-step UI flows (Campaign Creation)
├── config/               # Configuration files
│   └── config.yaml
├── core/                 # Core simulation logic (auction, bidding, etc.)
├── data_models/          # Pydantic schemas
├── features/             # High-level functionalities (attribution, targeting)
├── services/             # External API clients (Google Ads, Gemini)
├── .streamlit/           # Streamlit secrets management
│   └── secrets.toml
├── main.py               # Main application entry point
├── README.md             # This file
└── requirements.txt      # Python dependencies
Setup and Installation
Follow these steps to get the application running locally.

Prerequisites:

Python 3.8+

Access to Google Ads, Google Gemini, and Dialogflow APIs (optional, but recommended for full functionality)

1. Clone the Repository (or use the provided files)

2. Create a Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies.

Bash

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
3. Install Dependencies
Install all required Python packages from the requirements.txt file.

Bash

pip install -r requirements.txt
Configuration
You must provide API credentials for the application to connect to external services.

1. Google Ads API Credentials (config.yaml)
Fill in your Google Ads API credentials in the config/config.yaml file:

YAML

google_ads:
  client_id: "YOUR_CLIENT_ID"
  client_secret: "YOUR_CLIENT_SECRET"
  developer_token: "YOUR_DEVELOPER_TOKEN"
  login_customer_id: "123-456-7890" # Your Google Ads Manager Account ID (MCC)
  refresh_token: "YOUR_REFRESH_TOKEN"
  use_proto_plus: true
2. Gemini and Dialogflow Credentials (.streamlit/secrets.toml)
Create a file at .streamlit/secrets.toml and add your API keys for Google Gemini and Dialogflow:

Ini, TOML

# .streamlit/secrets.toml

gemini:
  api_key = "YOUR_GOOGLE_GEMINI_API_KEY"

dialogflow:
  project_id = "YOUR_DIALOGFLOW_PROJECT_ID"
  agent_id = "YOUR_DIALOGFLOW_AGENT_ID"
Note: The application will fall back to mock data and disable AI features if these credentials are not provided.

Running the Application
Once the installation and configuration are complete, run the Streamlit app from the project's root directory:

Bash

streamlit run main.py
The application will open in your default web browser.