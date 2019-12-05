import json

from aiohttp import web
from aiohttp.web import (
    Request,
    Response,
    HTTPBadRequest,
    HTTPForbidden,
    WebSocketResponse,
)

from typing import Tuple, Dict


async def handle(request: Request):
    auth_uid, repo = await parse_params(request)
    if auth_uid not in request.app.config["auth_users"]:  # type: ignore
        raise HTTPForbidden()

    base_user_dict: Dict[str, str] = {
        "user_uid": auth_uid,
        "repo_addr": repo,
    }
    ws: WebSocketResponse = WebSocketResponse()
    await ws.prepare(request)
    await send_to_mq(auth_uid, json.dumps(base_user_dict))
    await run_ansible_start_container(auth_uid, repo)

    await mq_pooler(ws, auth_uid)

    ws.close()
    return ws


async def send_frontend(request: Request) -> Response:
    raise NotImplementedError()


async def parse_params(request: Request) -> Tuple[str, str]:
    body = await request.json()
    auth_uid, repo = body.get("user_id"), body.get("repo_addr")
    if auth_uid and repo:
        return auth_uid, repo
    else:
        raise HTTPBadRequest(text="No options auth_uid or repo!")


async def run_ansible_start_container(auth_uid: str, repo_addr: str):
    raise NotImplementedError()


async def run_ansible_destroy_container():
    raise NotImplementedError()


async def send_to_mq(auth_uid: str, message: str):
    await create_recieve_queue(auth_uid)
    raise NotImplementedError()


async def create_recieve_queue(auth_uid: str):
    raise NotImplementedError()


async def mq_pooler(ws: WebSocketResponse, auth_uid):
    raise NotImplementedError()


def inject_config(app: web.Application, filename: str = "setting.json"):
    with open(filename) as config_file:
        config = json.load(config_file)
        app.config = config


if __name__ == "__main__":
    app = web.Application()
    inject_config(app)
    app.add_routes([web.get("/", send_frontend), web.post("/post", handle)])
    web.run_app(app)
