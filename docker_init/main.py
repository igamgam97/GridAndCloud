import logging
import sys
import subprocess
import json
from typing import Dict, List

from azure.servicebus import QueueClient, Message


def get_message(channel: str, conn_string: str) -> Dict[str, str]:
    q = QueueClient.from_connection_string(conn_string, channel)
    with q.get_receiver() as qr:
        messages = qr.fetch_next(timeout=30)
        message = str(messages[0])
        json_message = json.loads(message)
        return json_message


def run_sh(command: List[str]) -> str:
    result = subprocess.run(command, capture_output=True)
    if result.stdout:
        return result.stdout.decode("utf-8")
    raise Exception()


def send_message(channel: str, out_message: Dict[str, str], conn_string: str):
    q = QueueClient.from_connection_string(conn_string, channel)
    json_message = Message(json.dumps(out_message).encode("utf-8"))
    q.send(json_message)


if __name__ == "__main__":
    channel = "incoming"
    from conn_string import conn
    message = get_message(channel, conn)
    try:
        out_channel_name = message["auth_uid"]
        repo = message["repo"]
    except KeyError:
        logging.error("no expected fields in request message")
        sys.exit(1)

    command = ["/usr/bin/git", "clone", f"{repo}", "/src"]
    try:
        run_sh(command)
    except Exception:
        logging.error("something wrong in bash command")
        sys.exit(1)

    command = [
        "java",
        "-jar",
        "/detekt/detekt-cli-1.2.1-all.jar",
        "-i",
        "/src",
        "-r",
        "html:/result.html",
    ]
    try:
        run_sh(command)
    except Exception:
        logging.error("something wrong in bash command")
        sys.exit(1)

    with open("/result.html") as html:
        result = html.read()
        out_message = {"result": result}
        send_message(out_channel_name, out_message, conn)
    sys.exit(0)
