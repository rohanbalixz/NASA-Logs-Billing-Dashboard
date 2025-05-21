# NASA Logs Billing Demo

A deployable credit-billing demo that processes NASA HTTP logs as billable events and provides usage visualization.

## Features

- 🔄 Real-time event ingestion
- 📊 Interactive usage dashboard
- 💰 Credit-based billing
- 📈 Usage visualization with Plotly
- 🐳 Docker containerization

## Quick Start

1. **Build the Docker image:**
   ```bash
   docker build -t billing-demo .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 billing-demo
   ```

3. **Access the dashboard:**
   Open http://localhost:8000 in your browser

## Processing NASA Logs

1. Place your NASA log file as `access.log` in the project root
2. Run the parser:
   ```bash
   python parse_nasa_logs.py
   ```
   This will generate `events.jsonl` with processed billing events.

## API Endpoints

- `GET /usage?start=YYYY-MM-DD&end=YYYY-MM-DD`
  - Get usage data and invoice for a date range
  - Optional: `customer_id` query parameter

- `POST /event`
  - Ingest a single billing event
  - Body:
    ```json
    {
      "customer_id": "demo_user",
      "timestamp": "2025-05-20T14:23:00Z",
      "credits": 1
    }
    ```

## Development

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the development server:
   ```bash
   uvicorn app:app --reload
   ```

## Pricing Rules

- Base credits: 1 credit per request
- Additional credits: 1 credit per KB served
- USD conversion: $0.001 per credit

## Architecture

- `pricing.py`: Credit computation rules
- `parse_nasa_logs.py`: Log parser and event generator
- `billing_engine.py`: Core billing logic
- `app.py`: FastAPI web service
- `templates/index.html`: Dashboard UI

## Deployment

The application is containerized and can be deployed to:
- Heroku
- Google Cloud Run
- AWS ECS
- Any platform supporting Docker containers

## License

MIT 