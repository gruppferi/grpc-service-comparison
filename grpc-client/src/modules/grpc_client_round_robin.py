import os
import random
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
import grpc
from modules.proto import fibonacci_pb2, fibonacci_pb2_grpc
from modules.logger import get_logger

app = Flask(__name__)
logger = get_logger(__name__, log_level="INFO")
headless_service_dns = os.environ.get('SERVER_NAME', 'localhost')
grpc_server_port = os.environ.get('SERVER_PORT', '50051')
grpc_server_svc_type = os.environ.get('GRPC_SERVER_SVC_TYPE', 'normal')
workers = int(os.environ.get('WORKERS', '1'))

def create_grpc_channel(headless_service_dns, grpc_server_port):
    """
    Creates a gRPC channel with round-robin load balancing.

    Parameters:
    headless_service_dns (str): The DNS address of the gRPC server.
    grpc_server_port (str): The port number on which the gRPC server is running.

    Returns:
    grpc.Channel: The created gRPC channel.
    """
    if grpc_server_svc_type == "normal":
        target_uri = f'{headless_service_dns}:{grpc_server_port}'
        channel = grpc.insecure_channel(target_uri)
        logger.debug(f"Created gRPC channel with normal Kubernetes svc to target: {target_uri}")
        return channel
    elif grpc_server_svc_type == "headless":
        target_uri = f'dns:///{headless_service_dns}:{grpc_server_port}'
        channel = grpc.insecure_channel(target_uri, options=[
            ('grpc.lb_policy_name', 'round_robin')
        ])
        logger.debug(f"Created gRPC channel with round-robin load balancing to target: {target_uri}")
        return channel

channel = create_grpc_channel(headless_service_dns, grpc_server_port)

def handle_grpc_request(stub, grpc_request):
    """
    Handles a single gRPC request.

    Parameters:
    stub (grpc.Stub): The gRPC stub to use for the request.
    grpc_request: The gRPC request to send.

    Returns:
    The gRPC response.
    """
    return stub.Fibonacci(grpc_request)

@app.route('/increment', methods=['GET'])
def handle_request():
    """
    Handles the `/increment` route.

    This route makes `iteration` number of gRPC requests to increment a number.
    The `iteration` parameter specifies how many requests to make (default is 1).
    Returns a JSON list of responses from the gRPC server.

    Parameters:
    iteration (int): Number of iterations for the gRPC request, specified via query parameter (default is 1).

    Returns:
    Response: A JSON response containing a list of server names and the responses from each server.
    """
    iteration = int(request.args.get('iteration', 1))
    pod_name = os.environ.get('POD_NAME', 'client')
    stub = fibonacci_pb2_grpc.FibonacciServiceStub(channel)
    responses = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(handle_grpc_request, stub, fibonacci_pb2.IncrementRequest(name=pod_name)) for _ in range(iteration)]

        for future in concurrent.futures.as_completed(futures):
            response = future.result()
            responses.append({'server': response.server_name, 'response': response.number})
            logger.info(f"Server: {response.server_name} Response: {response.number}")

    return jsonify(responses)

@app.route('/fibonacci', methods=['GET'])
def handle_fibonacci_request():
    """
    Handles the `/fibonacci` route.

    This route calculates the Fibonacci number for a given input `n` using gRPC requests.
    Returns a JSON response with the server name and the calculated Fibonacci value.

    Parameters:
    n (int): The position of the Fibonacci sequence to calculate, specified via query parameter (default is 1).

    Returns:
    Response: A JSON response containing the server name and the calculated Fibonacci value.
    """
    n = int(request.args.get('n', 1))
    stub = fibonacci_pb2_grpc.FibonacciServiceStub(channel)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        grpc_request = fibonacci_pb2.FibonacciRequest(n=n)
        future = executor.submit(handle_grpc_request, stub, grpc_request)
        response = future.result()

    logger.info(f"Server: {response.server_name} Fibonacci Value: {response.value}")
    return jsonify({'server': response.server_name, 'value': response.value})

@app.route('/fibonacci/random', methods=['GET'])
def handle_fibonacci_random():
    """
    Handles the `/fibonacci/random` route.

    This route calculates random Fibonacci numbers within a specified range.
    The number of iterations is specified via query parameter.

    Parameters:
    iterations (int): The number of random Fibonacci numbers to calculate, specified via query parameter (default is 1).
    fibo_start (int): The start of the range for random Fibonacci numbers (default is 1).
    fibo_end (int): The end of the range for random Fibonacci numbers (default is 10).

    Returns:
    Response: A JSON response containing the server name, the input value `n`, and the calculated Fibonacci value.
    """
    iterations = int(request.args.get('iterations', 1))
    fibo_start = int(request.args.get('fibo_start', 1))
    fibo_end = int(request.args.get('fibo_end', 10))
    response_data = request.args.get('output', 'true').lower() == 'true'

    iterations = int(request.args.get('iterations', 1))
    fibo_start = int(request.args.get('fibo_start', 1))
    fibo_end = int(request.args.get('fibo_end', 10))
    response_data = request.args.get('output', 'true').lower() == 'true'
    stub = fibonacci_pb2_grpc.FibonacciServiceStub(channel)

    responses = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_n_pairs = [
            (n := random.randint(fibo_start, fibo_end), executor.submit(handle_grpc_request, stub, fibonacci_pb2.FibonacciRequest(n=n)))
            for _ in range(iterations)
        ]

        responses = []

        for n, future in future_n_pairs:
            response = future.result()
            responses.append({
                'server': response.server_name,
                'n': n,
                'value': response.value
            })
            logger.info(f"Server: {response.server_name} Fibonacci Value for n={n}")

    if response_data:
        return jsonify(responses)
    else:
        return jsonify({"sergeant job done?": "Yes lieutenant!"})
