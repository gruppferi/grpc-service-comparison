import os
from concurrent import futures
import grpc
from prometheus_client import start_http_server, Counter
from modules.proto import fibonacci_pb2, fibonacci_pb2_grpc
from modules.logger import get_logger

request_counter = Counter('grpc_requests_total', 'Total number of gRPC requests', ['method', 'server_name', 'mode'])

class FibonacciService(fibonacci_pb2_grpc.FibonacciServiceServicer):
    """
    A gRPC service class that implements the Fibonacci service.

    This class handles two types of requests:
    - `Increment`: Increments a counter and returns the current value.
    - `Fibonacci`: Calculates the Fibonacci number for a given input `n`.

    Attributes:
    counter (int): A counter used in the `Increment` method to track the number of requests.
    logger: A logger for logging information about requests and server status.
    server_name (str): The name of the server, used in responses and logging.
    mode (str): The mode of the server, used in responses and logging.

    Methods:
    Increment(request, context): Handles Increment requests and returns the current counter value.
    Fibonacci(request, context): Handles Fibonacci requests and returns the Fibonacci value for the given input `n`.
    serve(): Starts the gRPC server and the Prometheus metrics server.
    """

    def __init__(self):
        """
        Initializes the Fibonacci service.

        Initializes the logger, counter, server name, and mode.
        """
        self.counter = 0
        self.logger = get_logger(__name__, log_level="INFO")
        self.server_name = os.environ.get('POD_NAME', "server")
        self.mode = os.environ.get('MODE', "Normal")
        self.workers = int(os.environ.get('WORKERS', 1))

    def Increment(self, request, context):
        """
        Handles Increment requests.

        Increments the internal counter and returns the new counter value.

        Parameters:
        request (fibonacci_pb2.IncrementRequest): The gRPC request object containing the client name.
        context: The gRPC context.

        Returns:
        fibonacci_pb2.IncrementResponse: The response containing the new counter value and the server name.
        """
        request_counter.labels(method='Increment', server_name=self.server_name, mode=self.mode).inc()

        self.counter += 1
        self.logger.info(f"Server: {self.server_name} Answered to client {request.name} with number {self.counter}")
        return fibonacci_pb2.IncrementResponse(number=self.counter, server_name=self.server_name)

    def Fibonacci(self, request, context):
        """
        Handles Fibonacci requests.

        Calculates the Fibonacci number for the given input `n`.

        Parameters:
        request (fibonacci_pb2.FibonacciRequest): The gRPC request object containing the Fibonacci position `n`.
        context: The gRPC context.

        Returns:
        fibonacci_pb2.FibonacciResponse: The response containing the calculated Fibonacci value and the server name.
        """
        request_counter.labels(method='Fibonacci', server_name=self.server_name, mode=self.mode).inc()

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

        result = fibonacci(request.n)
        self.logger.debug(f"Server: {self.server_name} Answered to client with Fibonacci({request.n}) = {result}")
        self.logger.info(f"Server: {self.server_name} Answered to client with Fibonacci({request.n})")


        return fibonacci_pb2.FibonacciResponse(value=str(result), server_name=self.server_name)

    def serve(self):
        """
        Starts the gRPC server and the Prometheus metrics server.

        The gRPC server listens on `0.0.0.0:50051`, and the Prometheus metrics server listens on `0.0.0.0:8000`.
        """
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=self.workers))
        fibonacci_pb2_grpc.add_FibonacciServiceServicer_to_server(FibonacciService(), server)
        server_address = '0.0.0.0:50051'
        server.add_insecure_port(server_address)
        server.start()
        self.logger.info(f"Server started on {server_address}")

        metrics_address = '0.0.0.0:8000'
        start_http_server(8000)
        self.logger.info(f"Metrics server started on {metrics_address}")

        server.wait_for_termination()
