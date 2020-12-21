from views import vk_view


def setup_routes(app):
    app.router.add_post("/vk", vk_view)
