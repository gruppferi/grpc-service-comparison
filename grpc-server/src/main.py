from modules.grpc_server import FibonacciService
if __name__ == '__main__':
    server = FibonacciService()
    server.serve()
