import logging
import sys
import subprocess
from typing import Dict


def get_meggase(channel: str) -> Dict[str, str]:
    raise NotImplementedError()


def run_sh(command: str) -> str:
    result = subprocess.run([command], capture_output=True)
    if result.stdout:
        return result.stdout.decode("utf-8")
    raise Exception()


def send_message(channel: str, out_message):
    raise NotImplementedError()


if __name__ == "__main__":
    channel = ""
    message = get_meggase(channel)
    try:
        out_channel_name = message["auth_uid"]
        repo = message["repo"]
    except KeyError:
        logging.error("no expected fields in request message")
        sys.exit(1)

    command = f"/usr/bin/git clone {repo} /src"
    try:
        result = run_sh(command)
    except Exception:
        logging.error("something wrong in bash command")
        sys.exit(1)

    out_message = {"result": result}
    send_message(out_channel_name, out_message)
    sys.exit(0)
