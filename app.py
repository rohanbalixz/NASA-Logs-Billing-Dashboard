from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, Dict, Any
import json
import logging
import traceback

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="Billing Demo API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize billing engine
try:
    from billing_engine import BillingEngine
    billing_engine = BillingEngine('events.jsonl')
except Exception as e:
    logger.error(f"Failed to initialize billing engine: {e}")
    logger.error(traceback.format_exc())
    raise

class Event(BaseModel):
    customer_id: str
    timestamp: datetime
    credits: int

@app.get("/")
async def root(request: Request):
    """Serve the main dashboard page."""
    start_date, end_date = billing_engine.get_available_date_range()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "start_date": start_date,
            "end_date": end_date
        }
    )

@app.get("/date-range")
async def get_date_range():
    """Get the available date range for the dataset."""
    start_date, end_date = billing_engine.get_available_date_range()
    return {
        "start_date": start_date,
        "end_date": end_date
    }

@app.get("/usage")
async def get_usage(
    start: str,
    end: str,
    customer_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get usage data and invoice for a date range.
    
    Args:
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        customer_id: Optional customer ID to filter by
    """
    logger.debug(f"Received usage request: start={start}, end={end}, customer_id={customer_id}")
    
    try:
        # Validate date format
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(end, '%Y-%m-%d')
        except ValueError as e:
            logger.error(f"Date validation error: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {str(e)}. Use YYYY-MM-DD"
            )
            
        # Validate date range
        if end_date < start_date:
            raise HTTPException(
                status_code=400,
                detail="End date must be after start date"
            )
            
        # Generate invoice
        try:
            invoice = billing_engine.generate_invoice(start, end, customer_id)
        except Exception as e:
            logger.error(f"Invoice generation error: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate invoice: {str(e)}"
            )
        
        # Get daily usage data
        try:
            usage_data = billing_engine.get_usage_data(start, end, customer_id)
        except Exception as e:
            logger.error(f"Usage data error: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get usage data: {str(e)}"
            )
        
        if not usage_data:
            logger.warning(f"No usage data found for period {start} to {end}")
            return {
                "invoice": invoice.to_dict(),
                "usage_data": []
            }
            
        response_data = {
            "invoice": invoice.to_dict(),
            "usage_data": usage_data
        }
        logger.debug(f"Returning response: {response_data}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_usage: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/event")
async def ingest_event(event: Event) -> Dict[str, Any]:
    """
    Ingest a single billing event.
    
    This endpoint is for demo purposes and appends to the events.jsonl file.
    In production, you'd want to use a proper event streaming solution.
    """
    try:
        event_dict = {
            "customer_id": event.customer_id,
            "timestamp": event.timestamp.isoformat(),
            "credits": event.credits
        }
        
        # Append to events file
        with open('events.jsonl', 'a') as f:
            f.write(json.dumps(event_dict) + '\n')
            
        return {"status": "success", "event": event_dict}
    except Exception as e:
        logger.error(f"Event ingestion error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process event: {str(e)}"
        ) 