# QSR Online Reviews Analytics Dashboard

A comprehensive, interactive analytics dashboard for Quick Service Restaurant (QSR) managers, built with Streamlit and powered by Keboola data pipeline. This self-service analytics tool provides insights into customer reviews, sentiment analysis, location performance, and predictive alerts.

## 🍟 Features

- **Overview Dashboard**: Key metrics, star rating distribution, and review volume trends
- **NLP Insights**: Interactive word clouds, entity-attribute relationships, and sentiment analysis
- **Benchmarking**: Location performance comparison and competitive analysis
- **Predictive Alerts**: Early warning system for negative sentiment trends

## 🏗️ Architecture

The application follows a modular architecture for maintainability and scalability:

```
src/
├── app.py              # Main entry point and navigation
├── data.py             # Data handling and Keboola integration
├── utils.py            # Helper functions and constants
├── scripts/
│   ├── overview.py     # Overview dashboard
│   ├── nlp_insights.py # NLP analysis visualizations
│   ├── benchmarking.py # Location comparison tools
│   ├── predictive.py   # Predictive analytics
└── requirements.txt    # Python dependencies
```

## 📊 Expected Data Tables

The dashboard expects the following tables from your Keboola project:

### Core Tables
- **`out.c-MART.DM_REVIEW_LEVEL`** (`reviews`): Review-level data with sentiment analysis
- **`out.c-MART.DM_KEYWORD_LEVEL`** (`keywords`): Keyword frequency and analysis
- **`out.c-MART.DM_ENTITY_LEVEL`** (`entities`): Entity-attribute relationship results

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Keboola project with the required data tables
- Keboola Storage API token

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd demo-qsr
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure secrets**
   
   Copy the template secrets file and configure your Keboola credentials:
   ```bash
   cp .streamlit/secrets.toml.templ .streamlit/secrets.toml
   ```
   
   Edit `.streamlit/secrets.toml` with your actual values:
   ```toml
   kbc_token = "your-actual-kbc-project-token"
   kbc_url = "your-actual-kbc-project-url"
   reviews = 'out.c-MART.DM_REVIEW_LEVEL'
   keywords = 'out.c-MART.DM_KEYWORD_LEVEL'
   entities = 'out.c-MART.DM_ENTITY_LEVEL'
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 🔧 Configuration

### Required Environment Variables

The application requires the following configuration in your `.streamlit/secrets.toml`:

```toml
# Keboola Connection
kbc_token = "your-kbc-project-token"
kbc_url = "your-kbc-project-url"

# Data Table References
reviews = 'out.c-MART.DM_REVIEW_LEVEL'
keywords = 'out.c-MART.DM_KEYWORD_LEVEL'
entities = 'out.c-MART.DM_ENTITY_LEVEL'

# Optional: AI Assistant Configuration
ASSISTANT_ID = "your-assistant-id"
FILE_ID = "your-file-id"
LOGO_URL = "your-logo-url"
```

### Data Schema Requirements

#### Reviews Table (`out.c-MART.DM_REVIEW_LEVEL`)
Expected columns:
- `REVIEW_ID`: Unique review identifier
- `PLACE_ID`: Location identifier
- `REVIEW_DATE`: Review timestamp
- `RATING`: Star rating (1-5)
- `OVERALL_SENTIMENT`: Sentiment classification
- `REVIEW_TEXT`: Original review text

#### Keywords Table (`out.c-MART.DM_KEYWORD_LEVEL`)
Expected columns:
- `REVIEW_ID`: Review identifier
- `KEYWORD`: Extracted keyword
- `FREQUENCY`: Keyword frequency count
- `SENTIMENT`: Keyword sentiment score

#### Entities Table (`out.c-MART.DM_ENTITY_LEVEL`)
Expected columns:
- `REVIEW_ID`: Review identifier
- `ENTITY`: Named entity
- `ATTRIBUTE`: Entity attribute
- `COUNT`: Entity-attribute frequency

## 📈 Dashboard Features

### Overview Tab
- **Key Metrics**: Total locations, reviews, and average ratings
- **Rating Distribution**: Interactive bar chart showing star rating breakdown
- **Review Volume Trends**: Time-series analysis of review volume
- **Sentiment Overview**: Positive/negative sentiment distribution

### NLP Insights Tab
- **Interactive Word Cloud**: Visual representation of most frequent keywords
- **Entity Network Graph**: Network visualization of entity-attribute relationships
- **Sentiment Analysis**: Detailed sentiment breakdown by entity and attribute

### Benchmarking Tab
- **Location Performance**: Sortable table comparing location metrics
- **Geographic Analysis**: Performance by state, city, and location
- **Competitive Insights**: Cross-location comparison tools

### Predictive Alerts Tab
- **Trend Analysis**: Rolling average sentiment trends
- **Early Warning System**: Identification of locations with negative sentiment trends
- **Alert Thresholds**: Configurable alert parameters

## 🚀 Deployment

### Local Development
```bash
streamlit run app.py
```

### Keboola Data App Deployment
1. Fork this repository to your GitHub account
2. Configure your Keboola project with the required data tables
3. Set up the secrets configuration in Keboola
4. Deploy as a Keboola Data App using the GitHub repository URL

### Environment Variables
Ensure all required environment variables are set in your deployment environment:
- `KEBOOLA_TOKEN`: Your Keboola Storage API token
- `KEBOOLA_URL`: Your Keboola project URL
- Additional configuration as specified in the secrets template

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the [Issues](../../issues) page for existing solutions
- Create a new issue for bugs or feature requests
- Review the Keboola documentation for data pipeline setup

## 🔗 Related Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Keboola Documentation](https://help.keboola.com/)

---

**Note**: This dashboard is designed to work with processed data from a Keboola data pipeline. Ensure your data pipeline is properly configured and the required tables are available before deploying the dashboard. 