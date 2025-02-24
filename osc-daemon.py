# osc_daemon.py
import asyncio
import json
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher

class OSCDaemon:
    def __init__(self, socket_host='127.0.0.1', socket_port=65432,
                 osc_send_host='127.0.0.1', osc_send_port=57120,
                 osc_receive_host='127.0.0.1', osc_receive_port=57121):
        # Socket settings for MCP communication
        self.socket_host = socket_host
        self.socket_port = socket_port
        
        # OSC settings
        self.osc_send_host = osc_send_host
        self.osc_send_port = osc_send_port
        self.osc_receive_host = osc_receive_host
        self.osc_receive_port = osc_receive_port
        
        # Initialize OSC client
        self.osc_client = SimpleUDPClient(osc_send_host, osc_send_port)
        
        # Initialize OSC server dispatcher
        self.dispatcher = Dispatcher()
        self.dispatcher.set_default_handler(self.default_handler)
        
    async def start(self):
        """Start both the socket server and OSC server."""
        # Start OSC server
        self.osc_server = AsyncIOOSCUDPServer(
            (self.osc_receive_host, self.osc_receive_port),
            self.dispatcher,
            asyncio.get_event_loop()
        )
        await self.osc_server.create_serve_endpoint()
        
        # Start socket server
        server = await asyncio.start_server(
            self.handle_socket_client,
            self.socket_host,
            self.socket_port
        )
        print(f"Daemon listening on {self.socket_host}:{self.socket_port}")
        
        async with server:
            await server.serve_forever()
    
    def default_handler(self, address, *args):
        """Handle incoming OSC messages."""
        print(f"Received OSC: {address}: {args}")
        
    async def handle_socket_client(self, reader, writer):
        """Handle incoming socket connections from MCP server."""
        print("New connection from MCP server")
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                    
                message = json.loads(data.decode())
                command = message.get('command')
                
                if command == 'send_message':
                    address = message.get('address')
                    args = message.get('args', [])
                    self.osc_client.send_message(address, args)
                    response = {'status': 'sent'}
                elif command == 'get_status':
                    response = {
                        'status': 'ok',
                        'send_port': self.osc_send_port,
                        'receive_port': self.osc_receive_port
                    }
                else:
                    response = {'status': 'error', 'message': 'Unknown command'}
                
                writer.write(json.dumps(response).encode())
                await writer.drain()
                
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

if __name__ == "__main__":
    daemon = OSCDaemon()
    asyncio.run(daemon.start())
