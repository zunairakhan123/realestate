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

async def handle_lead_status_change(lead_data: dict):
    """
    Listens for any lead status change and logs a detailed status transition notification.
    """
    lead_id = lead_data.get("id")
    old_status = lead_data.get("old_status")
    new_status = lead_data.get("status")
    
    logger.info(f"EVENT RECEIVED: Lead {lead_id} status changing from '{old_status}' to '{new_status}'.")
    
    # Simulate network delay for sending notification (email/SMS/push)
    await asyncio.sleep(1) 
    
    logger.info(
        f"NOTIFICATION SENT: Lead status changed from \"{old_status}\" to \"{new_status}\"."
    )