import os
import asyncio
import grpc
from prometheus_client import start_http_server, Counter
from modules.proto import fibonacci_pb2, fibonacci_pb2_grpc
from modules.logger import get_logger

# Create a counter for tracking the number of gRPC requests
request_counter = Counter('grpc_requests_total', 'Total number of gRPC requests', ['method', 'server_name', 'mode'])

class FibonacciService(fibonacci_pb2_grpc.FibonacciServiceServicer):
    """
    A gRPC service class that implements the Fibonacci service using asynchronous programming.

    This class handles two types of requests:
    - `Increment`: Increments a counter and returns the current value.
    - `Fibonacci`: Calculates the Fibonacci number for a given input `n`.

    Attributes:
    counter (int): A counter used in the `Increment` method to track the number of requests.
    logger: A logger for logging information about requests and server status.
    server_name (str): The name of the server, used in responses and logging.
    mode (str): The mode of the server, used in responses and logging.
    """

    def __init__(self):
        """
        Initializes the Fibonacci service.

        Initializes the logger, counter, server name, and mode based on environment variables.
        """
        self.counter = 0
        self.logger = get_logger(__name__, log_level="INFO")
        self.server_name = os.environ.get('POD_NAME', "server")
        self.mode = os.environ.get('MODE', "Normal")
        self.workers = int(os.environ.get('WORKERS', 1))

    async def Increment(self, request, context):
        """
        Handles Increment requests asynchronously.

        Increments the internal counter and returns the new counter value.

        Parameters:
        request (fibonacci_pb2.IncrementRequest): The gRPC request object containing the client name.
        context: The gRPC context.

        Returns:
        fibonacci_pb2.IncrementResponse: The response containing the new counter value and the server name.
        """
        # Increment the request counter for Prometheus metrics
        request_counter.labels(method='Increment', server_name=self.server_name, mode=self.mode).inc()

        # Increment the counter and log the response
        self.counter += 1
        self.logger.info(f"Server: {self.server_name} responded to client {request.name} with number {self.counter}")

        # Return the response with the new counter value
        return fibonacci_pb2.IncrementResponse(number=self.counter, server_name=self.server_name)

    async def Fibonacci(self, request, context):
        """
        Handles Fibonacci requests asynchronously.

        Calculates the Fibonacci number for the given input `n`.

        Parameters:
        request (fibonacci_pb2.FibonacciRequest): The gRPC request object containing the Fibonacci position `n`.
        context: The gRPC context.

        Returns:
        fibonacci_pb2.FibonacciResponse: The response containing the calculated Fibonacci value and the server name.
        """
        # Increment the request counter for Prometheus metrics
        request_counter.labels(method='Fibonacci', server_name=self.server_name, mode=self.mode).inc()

        # Define the Fibonacci function
        def fibonacci(n):
            """
            Calculates the Fibonacci number for a given input `n`.

            Parameters:
            n (int): The Fibonacci position.

            Returns:
            int: The calculated Fibonacci value.
            """
            a, b = 0, 1
            for _ in range(n):
                a, b = b, a + b
            return a

        # Calculate the Fibonacci number in a separate thread using asyncio
        result = await asyncio.to_thread(fibonacci, request.n)

        # Log the response
        self.logger.info(f"Server: {self.server_name} responded to client with Fibonacci({request.n}) = {result}")

        # Return the response with the calculated Fibonacci value
        return fibonacci_pb2.FibonacciResponse(value=str(result), server_name=self.server_name)

    async def serve(self):
        """
        Starts the asynchronous gRPC server and the Prometheus metrics server.

        The gRPC server listens on `0.0.0.0:50051`, and the Prometheus metrics server listens on `0.0.0.0:8000`.
        """
        # Create an asynchronous gRPC server using grpc
        server = grpc.aio.server()

        # Add the FibonacciService to the server
        fibonacci_pb2_grpc.add_FibonacciServiceServicer_to_server(self, server)

        # Bind the server to the specified address
        server_address = '0.0.0.0:50051'
        server.add_insecure_port(server_address)

        # Start the asynchronous gRPC server
        await server.start()
        self.logger.info(f"Async gRPC server started on {server_address}")

        # Start the Prometheus metrics server
        metrics_address = '0.0.0.0:8000'
        start_http_server(8000)
        self.logger.info(f"Metrics server started on {metrics_address}")

        # Keep the server running indefinitely
        await server.wait_for_termination()
