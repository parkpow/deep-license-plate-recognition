import logging
from typing import Any, Optional

def get_header(header_name: str, json_data: dict[str, Any]) -> Optional[str]:
    
    header = json_data.get("webhook_header", {})
    return header.get(header_name)

def get_required_header(header_name: str, json_data: dict[str, Any]) -> Optional[str]:

    header_value = get_header(header_name, json_data)

    if header_value is None:
        logging.error(f"The '{header_name}' is required but was not provided in header.")
    
    return header_value