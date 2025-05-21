import re
from datetime import datetime
import json
from typing import Dict, Any, Generator
import logging
from pricing import compute_credits

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NASA log format regex
# Example: 199.72.81.55 - - [01/Jul/1995:00:00:01 -0400] "GET /history/apollo/ HTTP/1.0" 200 6245
LOG_PATTERN = r'(\S+) \S+ \S+ \[([\w:/]+\s[+\-]\d{4})\] "(\S+) (\S+) (\S+)" (\d{3}) (\d+|-)'

def parse_log_line(line: str) -> Dict[str, Any]:
    """Parse a single line of NASA log format."""
    try:
        match = re.match(LOG_PATTERN, line)
        if not match:
            return None
        
        ip, timestamp_str, method, path, protocol, status, bytes_str = match.groups()
        
        # Parse timestamp
        try:
            timestamp = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
        except ValueError:
            logger.warning(f"Failed to parse timestamp: {timestamp_str}")
            return None
        
        # Parse bytes
        bytes_served = int(bytes_str) if bytes_str != '-' else 0
        
        return {
            'customer_id': 'demo_user',  # Using a default customer ID
            'timestamp': timestamp.isoformat(),
            'bytes_served': bytes_served,
            'path': path,
            'method': method,
            'status': int(status)
        }
    except Exception as e:
        logger.warning(f"Failed to parse line: {e}")
        return None

def process_log_file(input_file: str, output_file: str) -> None:
    """
    Process NASA log file and output billing events.
    
    Args:
        input_file: Path to input log file
        output_file: Path to output JSONL file
    """
    logger.info(f"Processing log file: {input_file}")
    events_processed = 0
    
    # Try different encodings
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(input_file, 'r', encoding=encoding) as f_in, open(output_file, 'w', encoding='utf-8') as f_out:
                for line in f_in:
                    try:
                        line = line.strip()
                        if not line:
                            continue
                        
                        event = parse_log_line(line)
                        if event:
                            # Compute credits for the event
                            event['credits'] = compute_credits(event)
                            # Write to JSONL file - ensure proper formatting
                            json_str = json.dumps(event, ensure_ascii=False)
                            f_out.write(json_str + '\n')
                            events_processed += 1
                            
                            if events_processed % 10000 == 0:
                                logger.info(f"Processed {events_processed} events")
                    except Exception as e:
                        logger.warning(f"Error processing line: {e}")
                        continue
                
                logger.info(f"Completed processing {events_processed} events")
                return  # Successfully processed with this encoding
        except UnicodeDecodeError:
            logger.warning(f"Failed with encoding {encoding}, trying next...")
            continue
            
    logger.error("Failed to process file with any encoding")
    raise ValueError("Could not process log file with any supported encoding")

if __name__ == '__main__':
    process_log_file('access.log', 'events.jsonl') 