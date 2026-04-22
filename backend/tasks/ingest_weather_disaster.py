"""
Real-time Weather and Disaster Alert Ingestion

Continuously fetches weather data from Open-Meteo (free) and earthquake/disaster
alerts from USGS and GDACS. These feed risk dashboards and supply chain alerts.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import httpx

from backend.tasks.scheduler import BackgroundTask
from backend.db.cache import get_cache

logger = logging.getLogger(__name__)


class WeatherAlert(BaseModel):
    """Weather alert or observation."""
    location: str
    temperature: float
    condition: str
    humidity: int
    wind_speed: float
    alert_level: str  # "normal", "warning", "critical"
    timestamp: datetime


class DisasterAlert(BaseModel):
    """Earthquake or disaster alert."""
    event_type: str  # "earthquake", "flood", "storm", etc.
    location: str
    severity: int  # 1-5 scale
    latitude: float
    longitude: float
    description: str
    timestamp: datetime
    affected_region: Optional[str] = None


class WeatherDisasterIngestTask(BackgroundTask):
    """Ingest weather and disaster alerts."""
    
    # Key supply chain locations to monitor
    MONITORED_LOCATIONS = [
        {"name": "Shanghai", "lat": 31.2304, "lon": 121.4737},  # Major port
        {"name": "Singapore", "lat": 1.3521, "lon": 103.8198},  # Major port
        {"name": "Rotterdam", "lat": 51.9225, "lon": 4.4792},  # European port
        {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},  # US west coast port
        {"name": "Hong Kong", "lat": 22.3193, "lon": 114.1694},  # Major port
    ]
    
    def __init__(self, interval_seconds: int = 600):  # 10 minutes
        super().__init__(
            name="weather_disaster_ingest",
            interval_seconds=interval_seconds,
            priority=65,
        )
    
    async def execute(self) -> Dict[str, Any]:
        """Fetch weather and disaster alerts."""
        cache = await get_cache()
        
        # Fetch in parallel
        weather_results = await asyncio.gather(
            *[self._fetch_weather(loc) for loc in self.MONITORED_LOCATIONS],
            return_exceptions=True
        )
        
        disasters = await self._fetch_disaster_alerts()
        
        # Filter weather results
        weather_alerts = []
        weather_errors = []
        for result in weather_results:
            if isinstance(result, Exception):
                weather_errors.append(str(result))
            elif result:
                weather_alerts.extend(result)
        
        # Combine alerts
        all_alerts = {
            "weather": [a.model_dump() for a in weather_alerts],
            "disasters": [a.model_dump() for a in disasters],
            "timestamp": datetime.now().isoformat(),
        }
        
        # Cache with 10-minute TTL
        await cache.setex("alerts:active", 600, all_alerts)
        
        # Also cache per-location weather for faster access
        for location, alert in zip(self.MONITORED_LOCATIONS, weather_results):
            if not isinstance(alert, Exception) and alert:
                key = f"weather:{location['name'].lower()}"
                await cache.setex(key, 600, alert[0].model_dump())
        
        logger.info(
            f"Ingested weather alerts for {len(self.MONITORED_LOCATIONS)} "
            f"locations and {len(disasters)} disaster alerts"
        )
        
        return {
            "weather_alerts": len(weather_alerts),
            "disaster_alerts": len(disasters),
            "locations_monitored": len(self.MONITORED_LOCATIONS),
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _fetch_weather(self, location: Dict) -> Optional[List[WeatherAlert]]:
        """Fetch weather for a single location from Open-Meteo."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": location["lat"],
                        "longitude": location["lon"],
                        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                        "temperature_unit": "fahrenheit",
                    }
                )
                response.raise_for_status()
            
            data = response.json()
            current = data.get("current", {})
            
            # Map weather code to condition
            condition = self._map_weather_code(current.get("weather_code", 0))
            
            # Determine alert level based on weather
            alert_level = self._determine_alert_level(
                current.get("temperature_2m", 70),
                current.get("weather_code", 0),
                current.get("wind_speed_10m", 0),
            )
            
            alert = WeatherAlert(
                location=location["name"],
                temperature=current.get("temperature_2m", 70),
                condition=condition,
                humidity=current.get("relative_humidity_2m", 50),
                wind_speed=current.get("wind_speed_10m", 0),
                alert_level=alert_level,
                timestamp=datetime.now(),
            )
            
            return [alert]
        
        except Exception as e:
            logger.warning(f"Failed to fetch weather for {location['name']}: {e}")
            return None
    
    async def _fetch_disaster_alerts(self) -> List[DisasterAlert]:
        """Fetch disaster alerts from GDACS and USGS."""
        alerts = []
        
        # Fetch earthquake alerts from USGS
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson",
                )
                response.raise_for_status()
            
            data = response.json()
            
            for feature in data.get("features", [])[:5]:  # Top 5 recent earthquakes
                props = feature["properties"]
                coords = feature["geometry"]["coordinates"]
                
                magnitude = props.get("mag", 0)
                severity = min(5, max(1, int(magnitude)))  # Convert magnitude to 1-5 scale
                
                alert = DisasterAlert(
                    event_type="earthquake",
                    location=props.get("place", "Unknown"),
                    severity=severity,
                    latitude=coords[1],
                    longitude=coords[0],
                    description=f"Magnitude {magnitude} earthquake",
                    timestamp=datetime.fromtimestamp(props.get("time", 0) / 1000),
                )
                
                alerts.append(alert)
        
        except Exception as e:
            logger.warning(f"Failed to fetch earthquake alerts: {e}")
        
        return alerts
    
    @staticmethod
    def _map_weather_code(code: int) -> str:
        """Map WMO weather code to human-readable condition."""
        weather_map = {
            0: "Clear sky",
            1: "Mostly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }
        return weather_map.get(code, "Unknown")
    
    @staticmethod
    def _determine_alert_level(temp: float, weather_code: int, wind_speed: float) -> str:
        """Determine alert level based on weather conditions."""
        # Extreme temperatures
        if temp < -20 or temp > 115:
            return "critical"
        
        # Severe weather events
        if weather_code >= 95:  # Thunderstorm with hail
            return "critical"
        
        # Heavy snow/rain
        if weather_code in [65, 75, 82, 86]:
            return "warning"
        
        # High wind
        if wind_speed > 40:
            return "warning"
        
        # Moderate conditions
        if temp < 0 or temp > 100:
            return "warning"
        
        return "normal"
