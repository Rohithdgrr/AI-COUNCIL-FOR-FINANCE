"""
Viewport-Aware Streaming

Only stream data for dashboard panels currently visible to the user.
Reduces bandwidth, server load, and improves performance.
Strategy #10: Stream only what matters to the browser.
"""

import logging
from typing import Dict, List, Set, Optional, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class DashboardPanel(str, Enum):
    """Dashboard panel identifiers."""
    MARKET_TICKER = "market_ticker"
    RISK_DASHBOARD = "risk_dashboard"
    NEWS_FEED = "news_feed"
    WEATHER_ALERTS = "weather_alerts"
    COMMODITY_PRICES = "commodity_prices"
    SUPPLY_CHAIN_STATUS = "supply_chain_status"
    COUNCIL_DEBATE = "council_debate"
    FORECAST_ANALYSIS = "forecast_analysis"


class PanelStreamingManager:
    """Manage panel visibility and streaming subscriptions."""
    
    def __init__(self):
        # Per-session: which panels are visible
        self.visible_panels: Dict[str, Set[str]] = {}
        # Pan subscription change history
        self.change_log: Dict[str, List[Dict]] = {}
    
    def update_visible_panels(self, session_id: str, panels: List[str]) -> Dict[str, Any]:
        """
        Update which panels are visible for a user session.
        
        Called when user scrolls, resizes, or navigates dashboard.
        """
        visible_set = set(panels)
        
        # Get previous state
        prev_visible = self.visible_panels.get(session_id, set())
        
        # Find changes
        newly_visible = visible_set - prev_visible
        newly_hidden = prev_visible - visible_set
        still_visible = visible_set & prev_visible
        
        # Update state
        self.visible_panels[session_id] = visible_set
        
        # Log change
        if session_id not in self.change_log:
            self.change_log[session_id] = []
        
        self.change_log[session_id].append({
            "timestamp": datetime.now().isoformat(),
            "visible_count": len(visible_set),
            "newly_visible": list(newly_visible),
            "newly_hidden": list(newly_hidden),
        })
        
        return {
            "session_id": session_id,
            "visible_panels": list(visible_set),
            "newly_visible": list(newly_visible),
            "newly_hidden": list(newly_hidden),
            "still_visible": list(still_visible),
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_subscriptions(self, session_id: str) -> Set[str]:
        """Get topics to subscribe to for this session."""
        visible = self.visible_panels.get(session_id, set())
        
        # Map panels to WebSocket topics
        subscriptions = set()
        for panel in visible:
            subscriptions.update(self._panel_to_topics(panel))
        
        return subscriptions
    
    def _panel_to_topics(self, panel: str) -> Set[str]:
        """Map dashboard panel to WebSocket topics."""
        mapping = {
            DashboardPanel.MARKET_TICKER: {"DASHBOARD", "MARKET"},
            DashboardPanel.RISK_DASHBOARD: {"RISK", "DASHBOARD"},
            DashboardPanel.NEWS_FEED: {"RAG", "DASHBOARD"},
            DashboardPanel.WEATHER_ALERTS: {"DASHBOARD"},
            DashboardPanel.COMMODITY_PRICES: {"DASHBOARD", "MARKET"},
            DashboardPanel.SUPPLY_CHAIN_STATUS: {"RISK", "DASHBOARD"},
            DashboardPanel.COUNCIL_DEBATE: {"COUNCIL"},
            DashboardPanel.FORECAST_ANALYSIS: {"RAG", "DASHBOARD"},
        }
        return mapping.get(panel, {"DASHBOARD"})
    
    def get_priority_level(self, panel: str) -> int:
        """
        Get update priority for a panel.
        
        Higher = more frequent updates.
        Returns frequency in seconds.
        """
        priorities = {
            DashboardPanel.MARKET_TICKER: 30,        # Real-time
            DashboardPanel.RISK_DASHBOARD: 60,       # 1 min
            DashboardPanel.NEWS_FEED: 300,           # 5 min
            DashboardPanel.WEATHER_ALERTS: 600,      # 10 min
            DashboardPanel.COMMODITY_PRICES: 120,    # 2 min
            DashboardPanel.SUPPLY_CHAIN_STATUS: 120, # 2 min
            DashboardPanel.COUNCIL_DEBATE: 60,       # 1 min
            DashboardPanel.FORECAST_ANALYSIS: 300,   # 5 min
        }
        return priorities.get(panel, 300)
    
    def should_update_panel(
        self,
        session_id: str,
        panel: str,
        last_update_times: Dict[str, float],
    ) -> bool:
        """
        Check if panel should be updated based on priority and last update time.
        """
        import time
        
        # Skip if not visible
        if panel not in self.visible_panels.get(session_id, set()):
            return False
        
        priority = self.get_priority_level(panel)
        last_update = last_update_times.get(panel, 0)
        elapsed = time.time() - last_update
        
        return elapsed >= priority


class ViewportAwareSocket:
    """WebSocket connection with viewport-aware subscriptions."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.manager = PanelStreamingManager()
        self.subscribed_topics: Set[str] = set()
        self.last_update_times: Dict[str, float] = {}
    
    async def on_viewport_change(self, visible_panels: List[str]) -> Dict[str, Any]:
        """Handle viewport change event."""
        changes = self.manager.update_visible_panels(self.session_id, visible_panels)
        
        # Get required subscriptions
        new_subscriptions = self.manager.get_subscriptions(self.session_id)
        
        # Determine what changed
        topics_to_add = new_subscriptions - self.subscribed_topics
        topics_to_remove = self.subscribed_topics - new_subscriptions
        
        self.subscribed_topics = new_subscriptions
        
        return {
            "viewport_update": changes,
            "subscriptions": {
                "current": list(self.subscribed_topics),
                "added": list(topics_to_add),
                "removed": list(topics_to_remove),
            },
            "panel_priorities": {
                panel: self.manager.get_priority_level(panel)
                for panel in visible_panels
            },
        }
    
    async def broadcast_to_viewport(self, event_data: Dict[str, Any]) -> List[str]:
        """
        Broadcast event only to visible panels.
        
        Returns: List of panels that were updated.
        """
        import time
        
        updated_panels = []
        
        for panel in self.manager.visible_panels.get(self.session_id, set()):
            # Check if this panel should be updated
            if self.manager.should_update_panel(
                self.session_id,
                panel,
                self.last_update_times,
            ):
                # Panel would be updated
                updated_panels.append(panel)
                self.last_update_times[panel] = time.time()
        
        return updated_panels


class FrontendViewportTracker:
    """Frontend-side viewport tracking configuration."""
    
    # Intersection Observer options for viewport detection
    OBSERVER_OPTIONS = {
        "root": None,          # Use viewport as root
        "rootMargin": "100px", # Start loading 100px before visible
        "threshold": 0.1,      # Trigger when 10% visible
    }
    
    # Panels to track
    TRACKED_PANELS = [
        DashboardPanel.MARKET_TICKER,
        DashboardPanel.RISK_DASHBOARD,
        DashboardPanel.NEWS_FEED,
        DashboardPanel.WEATHER_ALERTS,
        DashboardPanel.COMMODITY_PRICES,
        DashboardPanel.SUPPLY_CHAIN_STATUS,
        DashboardPanel.COUNCIL_DEBATE,
        DashboardPanel.FORECAST_ANALYSIS,
    ]
    
    @staticmethod
    def get_configuration() -> Dict[str, Any]:
        """Get frontend configuration for viewport tracking."""
        return {
            "observer_options": FrontendViewportTracker.OBSERVER_OPTIONS,
            "panels": [p.value for p in FrontendViewportTracker.TRACKED_PANELS],
            "update_debounce_ms": 500,  # Debounce viewport changes
        }


# Global viewport manager
_viewport_managers: Dict[str, ViewportAwareSocket] = {}


def get_viewport_manager(session_id: str) -> ViewportAwareSocket:
    """Get or create viewport manager for session."""
    if session_id not in _viewport_managers:
        _viewport_managers[session_id] = ViewportAwareSocket(session_id)
    return _viewport_managers[session_id]


def cleanup_session(session_id: str) -> None:
    """Clean up viewport manager for session."""
    _viewport_managers.pop(session_id, None)
    logger.info(f"Cleaned up viewport manager for session {session_id}")


def get_frontend_config() -> Dict[str, Any]:
    """Get frontend configuration for viewport awareness."""
    return FrontendViewportTracker.get_configuration()
