import asyncio
from typing import Callable, Dict, List, Any

class EventBus:
    def __init__(self):
        # Stores event names and the functions waiting for them
        self.listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, listener: Callable):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)

    def emit(self, event_type: str, data: Any):
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                # Create an async task so the main thread isn't blocked!
                asyncio.create_task(listener(data))

# Instantiate the global event bus
event_bus = EventBus()