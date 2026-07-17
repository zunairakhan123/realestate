import asyncio
from app.core.logger import logger

async def handle_terminal_lead(lead_data: dict):
    """
    Listens for terminal lead events and simulates a notification.
    """
    logger.info(f"EVENT RECEIVED: Preparing notification for lead {lead_data['id']}")
    
    # Simulate network delay for sending an email/SMS
    await asyncio.sleep(2) 
    
    logger.info(
        f"NOTIFICATION SENT: Lead {lead_data['id']} reached terminal status '{lead_data['status']}'. "
        f"Agent {lead_data['agent_id']} has been notified."
    )