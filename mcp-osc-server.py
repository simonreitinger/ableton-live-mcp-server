
# mcp_osc_server.py
from mcp.server.fastmcp import FastMCP
import asyncio
import json
from typing import List, Optional
import socket

class OSCClient:
    """Client for communicating with the OSC daemon."""
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        
    def connect(self):
        """Connect to the OSC daemon."""
        if not self.connected:
            try:
                self.sock.connect((self.host, self.port))
                self.connected = True
                return True
            except Exception as e:
                print(f"Failed to connect to daemon: {e}")
                return False
                
    def send_command(self, command: dict) -> dict:
        """Send a command to the daemon and get response."""
        if not self.connected and not self.connect():
            return {'status': 'error', 'message': 'Not connected to daemon'}
            
        try:
            self.sock.sendall(json.dumps(command).encode())
            response = self.sock.recv(1024).decode()
            return json.loads(response)
        except Exception as e:
            self.connected = False
            return {'status': 'error', 'message': str(e)}
            
    def close(self):
        """Close the connection."""
        if self.connected:
            self.sock.close()
            self.connected = False

# Initialize the MCP server
mcp = FastMCP("OSC Controller", dependencies=["python-osc"])

# Create OSC client
osc_client = OSCClient()

@mcp.tool()
def send_osc(address: str, args: List[float]) -> str:
    """
    Send an OSC message.
    
    Args:
        address: OSC address pattern (e.g., '/test')
        args: List of argument values
    
    Returns:
        Status message
    """
    command = {
        'command': 'send_message',
        'address': address,
        'args': args
    }
    
    response = osc_client.send_command(command)
    if response['status'] == 'sent':
        return f"Sent OSC message to {address} with args {args}"
    else:
        return f"Error sending message: {response.get('message', 'Unknown error')}"

@mcp.tool()
def get_osc_status() -> str:
    """
    Get status of OSC connection.
    
    Returns:
        JSON string with connection status
    """
    command = {'command': 'get_status'}
    response = osc_client.send_command(command)
    return json.dumps(response, indent=2)

@mcp.prompt()
def osc_help() -> str:
    """Create a help prompt for OSC operations."""
    return """I can help you send OSC messages. You can:
1. Send messages to specific addresses with arguments
2. Check the OSC connection status

Example commands:
- "Send an OSC message to /test with arguments [1, 2, 3]"
- "Check the OSC connection status"

Note: Make sure the OSC daemon is running first!"""

if __name__ == "__main__":
    try:
        mcp.run()
    finally:
        osc_client.close()