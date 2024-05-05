from aiohttp import web
from modules.grpc_client_round_robin import handle_increment, handle_fibonacci, handle_fibonacci_random

async def create_app():
    app = web.Application()

    app.add_routes([
        web.get('/increment', handle_increment),
        web.get('/fibonacci', handle_fibonacci),
        web.get('/fibonacci/random', handle_fibonacci_random)
    ])
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)
