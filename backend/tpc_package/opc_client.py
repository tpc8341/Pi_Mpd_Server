# opc_client.py
# This file contains the OPC UA client logic to read data and store it in the database.
import asyncio
from asyncua import Client
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from tpc_package.wwt_database import WaterUsage, SessionLocal
import logging

# Configure logging for better visibility of OPC client operations.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# OPC UA Server details
OPC_SERVER_URL = "opc.tcp://192.168.90.216:49320"
OPC_TAG_NODE_ID = "ns=2;s=Channel1.Device1.WWT1"  # Node ID for the accumulated water usage tag
OPC_TICK_NODE_ID = "ns=2;s=Channel1.Device1.TICK" # Node ID for the health check tick tag

# --- OPC UA Authentication Credentials ---
# IMPORTANT: Replace these with your actual OPC UA server username and password.
OPC_USERNAME = "Administrator"
OPC_PASSWORD = "Aa123456"
# ---------------------------------------------

# --- OPC UA Server details ---
#OPC_SERVER_URL = "opc.tcp://192.168.15.15:4815"
#OPC_TAG_NODE_ID = "ns=3;s=Channel2.T3000.P-T-WWT-11A||XQ02"  # Node ID for the accumulated water usage tag
#OPC_TICK_NODE_ID = "ns=3;s=Channel2.T3000.DATE||XQ06" # Node ID for the health check tick tag

# --- OPC UA Authentication Credentials ---
#OPC_USERNAME = "OPCUAdata"
#OPC_PASSWORD = "OPCUAdata01!"
# ---------------------------------------------

# Interval for reading OPC tags.
READ_INTERVAL_SECONDS = 30
# Timeout in seconds for the tick tag.
TICK_TIMEOUT_SECONDS = 45

# --- Global variables for OPC connection status tracking ---
opc_status = "Connecting..."
opc_last_success_time = None
last_tick_value = None
last_tick_update_time = None
# ------------------------------------------------------------------

# --- NEW GLOBAL VARIABLE FOR PERSISTENT CLIENT ---
opc_client_instance = None


async def initialize_opc_client():
    """Initializes and connects the OPC UA client."""
    global opc_client_instance, opc_status
    
    opc_client_instance = Client(url=OPC_SERVER_URL)
    opc_client_instance.set_user(OPC_USERNAME)
    opc_client_instance.set_password(OPC_PASSWORD)
    
    try:
        await opc_client_instance.connect()
        logger.info("OPC UA Client successfully connected.")
        opc_status = "Normal"
        return True
    except Exception as e:
        logger.error(f"Failed to connect to OPC UA server: {e}")
        opc_status = "No Connection"
        opc_client_instance = None # Ensure client is None if connection fails
        return False


async def read_and_store_opc_data():
    """
    Reads the water usage and tick tags from the persistent client,
    stores the water usage data, and updates the global connection status.
    """
    global opc_status, opc_last_success_time, last_tick_value, last_tick_update_time, opc_client_instance
    
    if opc_client_instance is None:
        logger.info("Attempting to re-initialize OPC client.")
        await initialize_opc_client()
        if opc_client_instance is None:
            # Still failed to connect, exit and wait for next interval
            opc_status = "No Connection"
            return
            
    client = opc_client_instance # Use the persistent instance
    
    try:
        # --- 1. Read WWT1 (Water Usage) and store it ---
        # Get nodes *only* if they weren't fetched before (optional optimization, but we can keep it simple here)
        wwt_node = client.get_node(OPC_TAG_NODE_ID)
        data_value = await wwt_node.read_data_value()
        value = data_value.Value.Value
        timestamp = data_value.SourceTimestamp + timedelta(hours=8) # Use SourceTimestamp from the OPC server, add 8 hours to shift to timezone Asia/Taipei.

        # Create a new database session to store the water usage data
        db: Session = SessionLocal()
        try:
            new_record = WaterUsage(
                timestamp=timestamp,
                accumulated_value=float(value)
            )
            db.add(new_record)
            db.commit()
            logger.info(f"Stored water usage in DB: {value} at {timestamp}")
        except Exception as db_error:
            db.rollback()
            logger.error(f"Error storing data in database: {db_error}")
        finally:
            db.close()

        # --- 2. Read TICK tag for health check ---
        tick_node = client.get_node(OPC_TICK_NODE_ID)
        current_tick_value = await tick_node.get_value()

        # --- 3. Update status based on TICK value ---
        if last_tick_value is None or current_tick_value != last_tick_value:
            last_tick_value = current_tick_value
            last_tick_update_time = datetime.now()
            opc_status = "Normal"
            logger.info(f"Tick value updated to: {current_tick_value}. Status is Normal.")
        else:
            if last_tick_update_time and (datetime.now() - last_tick_update_time).total_seconds() > TICK_TIMEOUT_SECONDS:
                opc_status = "No Connection"
                logger.warning(f"Tick value has not changed in over {TICK_TIMEOUT_SECONDS} seconds. Status set to No Connection.")
                # Force client to disconnect on failure to allow re-initialization
                await client.disconnect()
                opc_client_instance = None
            else:
                if opc_status != "No Connection":
                    opc_status = "Normal"
                    
        # Update general success time
        opc_last_success_time = datetime.now()

    except Exception as e:
        logger.error(f"Error reading from OPC UA server (assuming connection loss): {e}")
        # Connection loss, set status to No Connection and allow re-initialization on next run
        opc_status = "No Connection"
        try:
            await client.disconnect() # Attempt clean disconnect
        except Exception:
            pass # Ignore disconnect error
        opc_client_instance = None
            
    finally:
        # The client is NOT disconnected here, it remains connected for the next read
        pass


async def opc_data_collector_task():
    """
    Runs the OPC data reading and storage function periodically.
    Initializes the client first.
    """
    # Attempt initial connection outside the loop
    await initialize_opc_client() 
    
    while True:
        await read_and_store_opc_data()
        await asyncio.sleep(READ_INTERVAL_SECONDS)