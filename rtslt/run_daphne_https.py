#!/usr/bin/env python
import ssl
import asyncio
from daphne.server import Server
from daphne.endpoints import build_endpoint_description_strings

async def main():
    # Create SSL context
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain('cert.pem', 'key.pem')
    
    # Build the application
    from rtslt.asgi import application
    
    # Create and run server
    server = Server(
        application=application,
        endpoints=build_endpoint_description_strings(
            host='0.0.0.0',
            port=8000,
            signal_handlers=True,
            action_text='started',
        ),
        ssl_context=ssl_context,
        verbosity=1,
        websocket_timeout=None,
        websocket_connect_timeout=None,
        command_line=True,
    )
    
    await server.run()

if __name__ == '__main__':
    asyncio.run(main())
