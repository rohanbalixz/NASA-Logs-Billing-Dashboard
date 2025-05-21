import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pricing import USD_PER_CREDIT
import logging
from collections import defaultdict
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BillingEvent:
    customer_id: str
    timestamp: datetime
    credits: int

@dataclass
class Invoice:
    customer_id: str
    period_start: str
    period_end: str
    total_credits: int
    amount_due_usd: float

    def to_dict(self) -> Dict:
        return {
            'customer_id': self.customer_id,
            'period_start': self.period_start,
            'period_end': self.period_end,
            'total_credits': self.total_credits,
            'amount_due_usd': self.amount_due_usd
        }

class BillingEngine:
    def __init__(self, events_file: str):
        self.events_file = events_file
        self.daily_totals: Dict[str, int] = {}  # Cache for daily totals
        self.date_range: Optional[Tuple[datetime, datetime]] = None
        self._load_and_aggregate_events()
        if not self.daily_totals:
            self._create_sample_data()

    def _create_sample_data(self):
        """Create sample billing events for July 1995."""
        logger.info("No events found, creating sample data")
        start_date = datetime(1995, 7, 1, tzinfo=timezone.utc)
        
        # Create events for each day in July with random credits
        for day in range(31):
            timestamp = start_date + timedelta(days=day)
            credits = random.randint(100, 500)  # Random credits between 100-500
            self.daily_totals[timestamp.astimezone(timezone(timedelta(hours=-4))).date().isoformat()] = credits
            
        # Save events to file
        try:
            with open(self.events_file, 'w') as f:
                for date, credits in self.daily_totals.items():
                    event_data = {
                        'customer_id': 'demo_user',
                        'timestamp': f"{date}T00:00:00-04:00",
                        'credits': credits
                    }
                    f.write(json.dumps(event_data) + '\n')
            logger.info(f"Created {len(self.daily_totals)} sample events")
        except Exception as e:
            logger.error(f"Failed to save sample events: {e}")

    def _load_and_aggregate_events(self):
        """Load events and pre-aggregate daily totals."""
        logger.info(f"Loading and aggregating events from {self.events_file}")
        daily_totals = defaultdict(int)
        min_date = None
        max_date = None
        
        try:
            with open(self.events_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        event_data = json.loads(line)
                        # Parse timestamp
                        timestamp = datetime.fromisoformat(event_data['timestamp'])
                        if timestamp.tzinfo is None:
                            timestamp = timestamp.replace(tzinfo=timezone.utc)
                            
                        # Update date range
                        if min_date is None or timestamp < min_date:
                            min_date = timestamp
                        if max_date is None or timestamp > max_date:
                            max_date = timestamp
                            
                        # Aggregate by date
                        date_key = timestamp.astimezone(timezone(timedelta(hours=-4))).date().isoformat()
                        daily_totals[date_key] += event_data['credits']
                        
                    except Exception as e:
                        logger.error(f"Error parsing line {line_num}: {e}")
                        logger.error(f"Line content: {line.strip()}")
                        continue
                        
            self.daily_totals = dict(daily_totals)
            self.date_range = (min_date, max_date)
            logger.info(f"Successfully aggregated {len(daily_totals)} days of data")
            logger.info(f"Date range: {min_date.date()} to {max_date.date()}")
            
        except Exception as e:
            logger.error(f"Failed to load events file: {e}")
            raise

    def generate_invoice(self, start_date: str, end_date: str, customer_id: Optional[str] = None) -> Invoice:
        """
        Generate an invoice for the specified period and customer.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            customer_id: Optional customer ID to filter by
            
        Returns:
            Invoice object
        """
        logger.info(f"Generating invoice for period {start_date} to {end_date}")
        
        # Calculate totals from pre-aggregated data
        total_credits = sum(
            credits
            for date, credits in self.daily_totals.items()
            if start_date <= date <= end_date
        )
        
        amount_due = total_credits * USD_PER_CREDIT
        
        logger.info(f"Generated invoice: {total_credits} credits, ${amount_due:.2f}")
        
        return Invoice(
            customer_id='demo_user',  # Using demo_user since we're pre-aggregating all users
            period_start=start_date,
            period_end=end_date,
            total_credits=total_credits,
            amount_due_usd=amount_due
        )

    def get_usage_data(self, start_date: str, end_date: str, customer_id: Optional[str] = None) -> List[Dict]:
        """
        Get daily usage data for visualization.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            customer_id: Optional customer ID to filter by
            
        Returns:
            List of daily usage records
        """
        # Initialize all dates in range with zero credits
        current = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        
        result = []
        while current <= end:
            date_key = current.isoformat()
            result.append({
                "date": date_key,
                "credits": self.daily_totals.get(date_key, 0)
            })
            current += timedelta(days=1)
            
        return result

    def get_available_date_range(self) -> Tuple[str, str]:
        """Get the available date range in YYYY-MM-DD format."""
        if not self.date_range:
            return ('1995-08-01', '1995-08-31')  # Default fallback
        
        start, end = self.date_range
        return (
            start.astimezone(timezone(timedelta(hours=-4))).date().isoformat(),
            end.astimezone(timezone(timedelta(hours=-4))).date().isoformat()
        ) 