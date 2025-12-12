"""
Lightweight event broadcasting system for agent coordination
Supports in-memory and can be swapped for Pub/Sub later
"""

import asyncio
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class Event:
    """Event data structure"""
    def __init__(self, name: str, data: Any, timestamp: Optional[datetime] = None):
        self.name = name
        self.data = data
        self.timestamp = timestamp or datetime.now()
        self.id = f"{name}_{self.timestamp.timestamp()}"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


class EventBus:
    """
    Simple event bus for agent coordination
    Can be swapped with Redis Pub/Sub or Google Pub/Sub later
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
    
    def subscribe(self, event_pattern: str, handler: Callable):
        """
        Subscribe to events
        
        Args:
            event_pattern: Event name or '*' for all events
            handler: Async function to handle event
        """
        if event_pattern not in self._subscribers:
            self._subscribers[event_pattern] = []
        
        self._subscribers[event_pattern].append(handler)
        logger.info(f"Subscribed handler to '{event_pattern}'")
    
    async def publish(self, event_name: str, data: Any):
        """
        Publish an event to all subscribers
        
        Args:
            event_name: Name of the event
            data: Event payload
        """
        event = Event(name=event_name, data=data)
        
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        logger.info(f"📢 Event published: {event_name}")
        
        # Notify specific subscribers
        handlers = self._subscribers.get(event_name, [])
        
        # Notify wildcard subscribers
        handlers.extend(self._subscribers.get("*", []))
        
        # Execute all handlers asynchronously
        tasks = []
        for handler in handlers:
            try:
                task = asyncio.create_task(handler(event))
                tasks.append(task)
            except Exception as e:
                logger.error(f"Error creating task for handler: {e}")
        
        # Wait for all handlers to complete (but don't block main flow)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_history(self, event_pattern: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Get recent event history"""
        if event_pattern:
            return [e for e in self._event_history if e.name.startswith(event_pattern)][-limit:]
        return self._event_history[-limit:]


# Global event bus instance
event_bus = EventBus()