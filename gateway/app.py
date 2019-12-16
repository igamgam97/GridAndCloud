import json
import logging
import sys
import os
import subprocess
from aiohttp import web
from aiohttp.web import (
    Request,
    HTTPBadRequest,
    HTTPForbidden,
    WebSocketResponse,
)
import uuid

from azure.servicebus import ServiceBusClient, QueueClient, Message

from typing import Tuple, Dict, List


async def handle(request: Request):
    auth_uid, repo = await parse_params(request)
    if auth_uid != "jiGVe0bRMBeo1BpYme0BjTiD2pC2":  # type: ignore
        raise HTTPForbidden()

    base_user_dict: Dict[str, str] = {
        "user_uid": auth_uid,
        "repo_addr": repo,
    }
    conn_string: str = os.getenv("CONN_STRING")
    ws: WebSocketResponse = WebSocketResponse()
    await ws.prepare(request)

    ws.send_str(json.dumps({"status": "CREATE QUEUE..."}))
    create_recieve_queue(auth_uid, conn_string)

    ws.send_str(json.dumps({"status": "SENDING MESSAGE..."}))
    send_to_mq(auth_uid, base_user_dict, conn_string)

    random_str = str(uuid.uuid4())

    ws.send_str(json.dumps({"status": "CREATE CONTAINER FOR YOU..."}))
    run_ansible_start_container(conn_string, random_str)

    ws.send_str(json.dumps({"status": "PROCESSING..."}))
    result = await wait_result(auth_uid, conn_string)

    ws.send_str(json.dumps({"status": "RESULT READY. DELETE CONTAINER..."}))
    delete_receive_queue(auth_uid, conn_string)
    run_ansible_destroy_container(random_str)

    ws.send_str(json.dumps({"status": "DONE"}.update(result)))

    ws.close()
    return ws


async def parse_params(request: Request) -> Tuple[str, str]:
    body = await request.json()
    auth_uid, repo = body.get("user_id"), body.get("repo_addr")
    if auth_uid and repo:
        return auth_uid, repo
    else:
        raise HTTPBadRequest(text="No options auth_uid or repo!")


async def run_ansible_start_container(conn_string: str, rand: str):
    command = [
        "ansible-playbook",
        "-i",
        "/app/inventory.yml",
        "/app/create_web_app.yml",
        "--extra-vars",
        f"conn_string={conn_string} random={rand}",
    ]
    try:
        run_sh(command)
    except Exception:
        logging.error("something wrong in bash command")
        sys.exit(1)


async def run_ansible_destroy_container(rand: str):
    command = [
        "ansible-playbook",
        "-i",
        "/app/inventory.yml",
        "/app/destroy_web_app.yml",
        "--extra-vars",
        f"random={rand}",
    ]
    try:
        run_sh(command)
    except Exception:
        logging.error("something wrong in bash command")
        sys.exit(1)


def send_to_mq(auth_uid: str, message: Dict[str, str], conn_string: str):
    q = QueueClient.from_connection_string(conn_string, auth_uid)
    json_message = Message(json.dumps(message).encode("utf-8"))
    q.send(json_message)


def create_recieve_queue(auth_uid: str, conn_string: str):
    sbc = ServiceBusClient.from_connection_string(conn_string)
    if not sbc.create_queue(auth_uid):
        logging.error("cannot create queue")
        sys.exit(1)


def delete_receive_queue(auth_uid: str, conn_string: str):
    sbc = ServiceBusClient.from_connection_string(conn_string)
    if not sbc.delete_queue(auth_uid):
        logging.error("cannot delete queue")
        sys.exit(1)


async def wait_result(auth_uid: str, conn_string: str) -> Dict[str, str]:
    q = QueueClient.from_connection_string(conn_string, auth_uid)
    async with q.get_receiver() as qr:
        messages = await qr.fetch_next(timeout=30)
        message = str(messages[0])
        json_message = json.loads(message)
        return json_message


if __name__ == "__main__":
    app = web.Application()
    app.add_routes([web.post("/post", handle)])
    web.run_app(app, port=8080, host="0.0.0.0")


def run_sh(command: List[str]) -> str:
    result = subprocess.run(command, capture_output=True)
    if result.stdout:
        return result.stdout.decode("utf-8")
    raise Exception()
