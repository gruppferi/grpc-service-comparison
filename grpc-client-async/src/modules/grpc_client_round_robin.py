import os
from aiohttp import web
import grpc
import random
from modules.proto import fibonacci_pb2, fibonacci_pb2_grpc
from modules.logger import get_logger

logger = get_logger(__name__, log_level="INFO")
headless_service_dns = os.environ.get('SERVER_NAME', 'localhost')
grpc_server_port = os.environ.get('SERVER_PORT', '50051')
grpc_server_svc_type = os.environ.get('GRPC_SERVER_SVC_TYPE', 'normal')
workers = int(os.environ.get('WORKERS', '1'))

async def create_grpc_channel():
    """
    Create and return a gRPC channel.

    Args:
        headless_service_dns (str): The DNS of the headless service to connect to.
        grpc_server_port (str): The port on which the gRPC server is running.

    Returns:
        grpc.aio.Channel: The created gRPC channel.
    """
    if grpc_server_svc_type == "normal":
        target_uri = f'{headless_service_dns}:{grpc_server_port}'
        channel = grpc.aio.insecure_channel(target_uri)
        logger.debug(f"Created gRPC channel with normal Kubernetes svc to target: {target_uri}")
        return channel
    elif grpc_server_svc_type == "headless":
        target_uri = f'dns:///{headless_service_dns}:{grpc_server_port}'
        channel = grpc.aio.insecure_channel(target_uri, options=[
            ('grpc.lb_policy_name', 'round_robin')
        ])
        logger.debug(f"Created gRPC channel with round-robin load balancing to target: {target_uri}")
        return channel

async def handle_increment(request):
    """
    Handle increment request by calling the Increment method of the gRPC service.

    Args:
        request (web.Request): The request object.

    Returns:
        web.Response: The JSON response containing the server name and incremented number.
    """
    pod_name = request.query.get('pod_name', 'client')
    iterations = int(request.query.get('iterations', '1'))
    channel = await create_grpc_channel()
    stub = fibonacci_pb2_grpc.FibonacciServiceStub(channel)

    responses = []
    for _ in range(iterations):
        response = await stub.Increment(fibonacci_pb2.IncrementRequest(name=pod_name))
        responses.append({'server': response.server_name, 'response': response.number})
        logger.info(f"Server: {response.server_name} Response: {response.number}")

    return web.json_response(responses)

async def handle_fibonacci(request):
    """
    Handle Fibonacci request by calling the Fibonacci method of the gRPC service.

    Args:
        request (web.Request): The request object.

    Returns:
        web.Response: The JSON response containing the server name and Fibonacci value.
    """
    n = int(request.query.get('n', '1'))
    channel = await create_grpc_channel()
    stub = fibonacci_pb2_grpc.FibonacciServiceStub(channel)

    response = await stub.Fibonacci(fibonacci_pb2.FibonacciRequest(n=n))
    logger.info(f"Server: {response.server_name} Fibonacci Value: {response.value}")
    return web.json_response({'server': response.server_name, 'value': response.value})

async def handle_fibonacci_random(request):
    """
    Handle Fibonacci random request by calling the Fibonacci method of the gRPC service with random values.

    Args:
        request (web.Request): The request object.

    Returns:
        web.Response: The JSON response containing the server name, random number, and Fibonacci value.
    """
    iterations = int(request.query.get('iterations', '1'))
    fibo_start = int(request.query.get('fibo_start', '1'))
    fibo_end = int(request.query.get('fibo_end', '10'))
    channel = await create_grpc_channel()
    stub = fibonacci_pb2_grpc.FibonacciServiceStub(channel)

    responses = []
    for _ in range(iterations):
        n = random.randint(fibo_start, fibo_end)
        response = await stub.Fibonacci(fibonacci_pb2.FibonacciRequest(n=n))
        responses.append({'server': response.server_name, 'n': n, 'value': response.value})
        logger.info(f"Server: {response.server_name} Fibonacci Value for n={n}")

    return web.json_response(responses)
