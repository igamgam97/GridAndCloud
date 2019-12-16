import json
import logging
import sys
import os
import subprocess
from flask import Flask, request, make_response
from werkzeug.exceptions import BadRequest
import uuid

from azure.cli.core import get_default_cli
from azure.servicebus import ServiceBusClient, QueueClient, Message

from typing import Tuple, Dict, List

app = Flask(__main__)

@app.route('/', methods=["POST"])
def handle(request: Request):
    auth_uid, repo = parse_params(request)
    if auth_uid != "jiGVe0bRMBeo1BpYme0BjTiD2pC2":  # type: ignore
        raise HTTPForbidden()

    base_user_dict: Dict[str, str] = {
        "user_uid": auth_uid,
        "repo_addr": repo,
    }
    from .conn_string import conn_string
    
    create_recieve_queue(auth_uid, conn_string)

    send_to_mq(auth_uid, base_user_dict, conn_string)

    random_str = str(uuid.uuid4())

    run_azure_start_container(conn_string, random_str)

    result = wait_result(auth_uid, conn_string)

    delete_receive_queue(auth_uid, conn_string)
    run_azure_destroy_container(random_str)

    return make_response(result)


def parse_params() -> Tuple[str, str]:
    body = request.json
    auth_uid, repo = body.get("user_id"), body.get("repo_addr")
    if auth_uid and repo:
        return auth_uid, repo
    else:
        raise BadRequest(text="No options auth_uid or repo!")


def run_azure_start_container(conn_string: str, rand: str):
    command = [
        "webapp",
        "create",
        "-n",
        f"app-{rand}",
        "-p",
        "base-service-plan",
        "-g",
        "base-resource-group",
        "-i",
        "igamgam97/detekt",
    ]
    try:
        run_azure(command)
    except Exception:
        logging.error("something wrong in bash command")
        sys.exit(1)


def run_azure_destroy_container(rand: str):
    command = [
        "webapp",
        "delete",
        "-n",
        f"app-{rand}",
        "-g",
        "base-resource-group",
    ]
    try:
        run_azure(command)
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


def wait_result(auth_uid: str, conn_string: str) -> Dict[str, str]:
    q = QueueClient.from_connection_string(conn_string, auth_uid)
    with q.get_receiver() as qr:
        messages = qr.fetch_next(timeout=30)
        message = str(messages[0])
        json_message = json.loads(message)
        return json_message


if __name__ == "__main__":
    app.run()


def run_azure(command: List[str]) -> str:
    response = get_default_cli().invoke(command)
    if response:
        return response
    raise Exception()
