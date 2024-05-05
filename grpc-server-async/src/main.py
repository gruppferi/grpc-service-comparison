import sys
import asyncio
import signal
from modules.grpc_server import FibonacciService

def main():
    server = FibonacciService()
    loop = asyncio.get_event_loop()

    # Define the signal handler function within the main function to capture the server instance
    def signal_handler(signum, frame):
        print(f"Received signal: {signum}")
        # Use loop in the context of this closure
        loop.run_until_complete(shutdown_server(server))
        loop.stop()
        sys.exit(0)

    # Register signal handlers for SIGINT and SIGTERM
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the server
    loop.run_until_complete(server.serve())

    # Run the event loop
    loop.run_forever()

    # Close the event loop
    loop.close()

# Function to gracefully shut down the server
async def shutdown_server(server):
    # Await graceful shutdown of the gRPC server
    await server.stop(grace=None)
    print("gRPC server has been shut down.")

# Entry point
if __name__ == '__main__':
    main()
