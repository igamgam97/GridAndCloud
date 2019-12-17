import json
import logging
import sys
import os
from flask import Flask, request, make_response, session, jsonify
from werkzeug.exceptions import BadRequest, Forbidden
import uuid

import time

from azure.cli.core import get_default_cli
from azure.common import AzureConflictHttpError
from azure.servicebus import ServiceBusClient, QueueClient, Message

from typing import Tuple, Dict, List

app = Flask(__name__)


def run_azure(command: List[str]):
    get_default_cli().invoke(command)


@app.route('/status', methods=['GET'])
def status():
    return jsonify(session['status'])


@app.route('/', methods=["POST"])
def handle():
    auth_uid, repo = parse_params()
    google_id = os.getenv("GOOGLE_ID")
    if auth_uid != google_id:  # type: ignore
        raise Forbidden()

    base_user_dict: Dict[str, str] = {
        "user_uid": auth_uid,
        "repo_addr": repo,
    }
    from conn_string import conn

    update_access_token()

    session['status'] = {'status': 'SENDING TO QUEUE'}
    create_recieve_queue(auth_uid, conn)

    send_to_mq(auth_uid, base_user_dict, conn)

    random_str = str(uuid.uuid4())

    session['status'] = {'status': 'UP YOUR CONTAINER'}
    run_azure_start_container(conn, random_str)

    session['status'] = {'status': 'PROCESS YOUR TASK'}

    result = wait_result(auth_uid, conn)
    session['status'] = {'status': 'RECEIVING RESULT'}

    delete_receive_queue(auth_uid, conn)
    run_azure_destroy_container(random_str)
    session['status'] = {'status': 'STOP CONTAINER'}

    return make_response(result)


def parse_params() -> Tuple[str, str]:
    body = request.json
    auth_uid, repo = body.get("user_id"), body.get("repo_addr")
    if auth_uid and repo:
        return auth_uid, repo
    else:
        raise BadRequest()


def update_access_token():
    app_id = os.getenv("APP_ID")
    password = os.getenv("PASSWORD")
    tenant = os.getenv("TENANT")
    command = [
        "login",
        "--service-principal",
        "--username",
        f"{app_id}",
        "--password",
        f"{password}",
        "--tenant",
        f"{tenant}"
    ]
    run_azure(command)


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
        "igamgam97/worker-app",
    ]
    run_azure(command)


def run_azure_destroy_container(rand: str):
    command = [
        "webapp",
        "delete",
        "-n",
        f"app-{rand}",
        "-g",
        "base-resource-group",
    ]
    run_azure(command)


def send_to_mq(auth_uid: str, message: Dict[str, str], conn_string: str):
    q = QueueClient.from_connection_string(conn_string, auth_uid)
    json_message = Message(json.dumps(message).encode("utf-8"))
    q.send(json_message)


def create_recieve_queue(auth_uid: str, conn_string: str):
    sbc = ServiceBusClient.from_connection_string(conn_string)
    try:
        sbc.create_queue(auth_uid)
    except AzureConflictHttpError:
        pass
    except Exception:
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
        messages = qr.fetch_next(timeout=500)
        message = str(messages[0])
        json_message = json.loads(message)
        return json_message


if __name__ == "__main__":
    from conn_string import conn
    try:
        create_recieve_queue('incoming', conn)
    except AzureConflictHttpError:
        pass
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'super secret key'
    app.run(port=8080, host='0.0.0.0')
