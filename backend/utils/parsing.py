"""Parsing utilities for extracting structured data from LLM responses."""

import re
from typing import Union


def parse_confidence(text: str, default: Union[float, int] = 50.0) -> Union[float, int]:
    """Extract confidence score from LLM response text.
    
    Supports multiple formats:
    - "confidence: 85"
    - "85/100"
    - "85% confidence"
    - "confidence score: 0.85"
    
    Args:
        text: The LLM response text to parse
        default: Default value if no confidence found
        
    Returns:
        Confidence score (0-100 scale or 0-1 scale depending on input)
    """
    patterns = [
        r"confidence[:\s]+(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*/\s*100",
        r"(\d+(?:\.\d+)?)\s*%\s*confidence",
        r"confidence\s+score[:\s]+(\d+(?:\.\d+)?)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            # Normalize to 0-100 scale if needed
            if value <= 1.0:
                value = value * 100
            # Return as int if default is int, else float
            return int(value) if isinstance(default, int) else min(value, 100.0)
    
    return default
