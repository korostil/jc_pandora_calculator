import logging

from aiohttp import web

from routes import setup_routes
from settings import config


async def make_app():
    app = web.Application()
    setup_routes(app)
    return app


if __name__ == "__main__":
    app = make_app()
    logging.basicConfig(level=logging.DEBUG)
    web.run_app(app, host=config["host"], port=config["port"])
