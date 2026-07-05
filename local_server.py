#!/usr/bin/env python3
import argparse
import asyncio
import base64
import dataclasses
import hashlib
import json
import logging
import os
import signal
import struct
import time
import urllib.parse
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
MAGIC_CLOSE = object()


@dataclasses.dataclass
class MessageRule:
    path: str | None = None
    kind: str = "any"
    contains: str | None = None
    equals: str | None = None
    json_key: str | None = None
    json_value: Any = None
    response_type: str = "text"
    response: Any = ""
    close_after: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "MessageRule":
        return cls(
            path=raw.get("path"),
            kind=raw.get("kind", "any"),
            contains=raw.get("contains"),
            equals=raw.get("equals"),
            json_key=raw.get("json_key"),
            json_value=raw.get("json_value"),
            response_type=raw.get("response_type", "text"),
            response=raw.get("response", ""),
            close_after=bool(raw.get("close_after", False)),
        )


@dataclasses.dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 7070
    expected_secret: str | None = None
    strict_secret: bool = False
    echo_text: bool = False
    echo_binary: bool = False
    log_binary_preview: int = 48
    welcome_text: str | None = None
    welcome_json: dict[str, Any] | None = None
    rules: list[MessageRule] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Connection:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    peer: str
    path: str
    query: dict[str, list[str]]
    headers: dict[str, str]
    role: str
    conn_id: str
    authenticated: bool = False
    secret_seen_in_message: bool = False


def load_server_config(path: str | None) -> ServerConfig:
    cfg = ServerConfig()
    if not path:
        return cfg

    with open(path, "rb") as f:
        if path.endswith(".toml"):
            if tomllib is None:
                raise RuntimeError("tomllib is not available in this Python build")
            raw = tomllib.load(f)
        else:
            raw = json.load(f)

    if "server" in raw:
        raw = raw["server"]

    cfg.host = raw.get("host", cfg.host)
    cfg.port = int(raw.get("port", cfg.port))
    cfg.expected_secret = raw.get("expected_secret")
    cfg.strict_secret = bool(raw.get("strict_secret", cfg.strict_secret))
    cfg.echo_text = bool(raw.get("echo_text", cfg.echo_text))
    cfg.echo_binary = bool(raw.get("echo_binary", cfg.echo_binary))
    cfg.log_binary_preview = int(raw.get("log_binary_preview", cfg.log_binary_preview))
    cfg.welcome_text = raw.get("welcome_text")
    cfg.welcome_json = raw.get("welcome_json")
    cfg.rules = [MessageRule.from_dict(item) for item in raw.get("rules", [])]
    return cfg


def extract_bind_target(config_path: str | None) -> tuple[str, int]:
    if not config_path or tomllib is None or not config_path.endswith(".toml"):
        return ("0.0.0.0", 7070)

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)
    rotom = raw.get("rotom", {})
    endpoint = rotom.get("rotom_worker_endpoint") or "ws://0.0.0.0:7070"
    parsed = urllib.parse.urlparse(endpoint)
    return (parsed.hostname or "0.0.0.0", parsed.port or 7070)


def make_accept_key(client_key: str) -> str:
    digest = hashlib.sha1((client_key + GUID).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


async def read_http_request(reader: asyncio.StreamReader) -> tuple[str, dict[str, str]]:
    request_line = await reader.readline()
    if not request_line:
        raise ConnectionError("empty request")

    try:
        request_line_text = request_line.decode("ascii").strip()
        method, target, _ = request_line_text.split(" ", 2)
    except ValueError as exc:
        raise ConnectionError("malformed request line") from exc

    if method.upper() != "GET":
        raise ConnectionError(f"unexpected method {method}")

    headers: dict[str, str] = {}
    while True:
        line = await reader.readline()
        if not line:
            raise ConnectionError("unexpected EOF while reading headers")
        if line == b"\r\n":
            break
        key, _, value = line.decode("utf-8", errors="replace").partition(":")
        headers[key.strip().lower()] = value.strip()

    return target, headers


async def send_http_error(writer: asyncio.StreamWriter, code: int, message: str) -> None:
    body = f"{code} {message}\n".encode("utf-8")
    writer.write(
        (
            f"HTTP/1.1 {code} {message}\r\n"
            f"Content-Type: text/plain\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Connection: close\r\n\r\n"
        ).encode("ascii")
        + body
    )
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def websocket_handshake(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> tuple[str, dict[str, str]]:
    target, headers = await read_http_request(reader)

    client_key = headers.get("sec-websocket-key")
    upgrade = headers.get("upgrade", "").lower()
    connection = headers.get("connection", "").lower()

    if upgrade != "websocket" or "upgrade" not in connection or not client_key:
        raise ConnectionError("not a websocket upgrade request")

    accept_key = make_accept_key(client_key)
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
    ).encode("ascii")

    writer.write(response)
    await writer.drain()
    return target, headers


async def read_frame(reader: asyncio.StreamReader) -> tuple[int, bytes]:
    first = await reader.readexactly(2)
    b1, b2 = first[0], first[1]

    fin = bool(b1 & 0x80)
    opcode = b1 & 0x0F
    masked = bool(b2 & 0x80)
    length = b2 & 0x7F

    if not fin:
        raise ConnectionError("fragmented frames are not supported")
    if not masked:
        raise ConnectionError("client frame was not masked")

    if length == 126:
        length = struct.unpack("!H", await reader.readexactly(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", await reader.readexactly(8))[0]

    mask = await reader.readexactly(4)
    payload = bytearray(await reader.readexactly(length))
    for i in range(length):
        payload[i] ^= mask[i % 4]
    return opcode, bytes(payload)


async def send_frame(writer: asyncio.StreamWriter, opcode: int, payload: bytes = b"") -> None:
    header = bytearray()
    header.append(0x80 | (opcode & 0x0F))
    size = len(payload)
    if size < 126:
        header.append(size)
    elif size < (1 << 16):
        header.append(126)
        header.extend(struct.pack("!H", size))
    else:
        header.append(127)
        header.extend(struct.pack("!Q", size))

    writer.write(bytes(header) + payload)
    await writer.drain()


def maybe_secret_from_headers(headers: dict[str, str]) -> str | None:
    for key in ("x-rotom-secret", "authorization", "sec-websocket-protocol"):
        value = headers.get(key)
        if value:
            return value
    return None


def maybe_secret_from_query(query: dict[str, list[str]]) -> str | None:
    for key in ("secret", "token", "auth", "rotom_secret"):
        values = query.get(key)
        if values:
            return values[0]
    return None


def inspect_json_fields(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def check_message_secret(payload_text: str, expected_secret: str) -> bool:
    if expected_secret in payload_text:
        return True
    payload_json = inspect_json_fields(payload_text)
    if not payload_json:
        return False

    for key in ("secret", "token", "auth", "authorization", "rotom_secret"):
        if payload_json.get(key) == expected_secret:
            return True
    return False


def preview_binary(payload: bytes, max_len: int) -> str:
    data = payload[:max_len]
    return data.hex()


def rule_matches(rule: MessageRule, conn: Connection, kind: str, text: str | None) -> bool:
    if rule.path and rule.path != conn.path:
        return False
    if rule.kind not in ("any", kind):
        return False
    if rule.equals is not None and text != rule.equals:
        return False
    if rule.contains is not None and (text is None or rule.contains not in text):
        return False
    if rule.json_key is not None:
        if text is None:
            return False
        parsed = inspect_json_fields(text)
        if not parsed or parsed.get(rule.json_key) != rule.json_value:
            return False
    return True


async def apply_rule(conn: Connection, rule: MessageRule) -> Any:
    response_type = rule.response_type
    response = rule.response

    if response_type == "json":
        await send_frame(conn.writer, 0x1, json.dumps(response).encode("utf-8"))
    elif response_type == "binary":
        await send_frame(conn.writer, 0x2, base64.b64decode(response))
    elif response_type == "close":
        await send_frame(conn.writer, 0x8, b"")
        return MAGIC_CLOSE
    else:
        await send_frame(conn.writer, 0x1, str(response).encode("utf-8"))

    if rule.close_after:
        await send_frame(conn.writer, 0x8, b"")
        return MAGIC_CLOSE
    return None


async def handle_connection(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    config: ServerConfig,
) -> None:
    peer_tuple = writer.get_extra_info("peername")
    peer = f"{peer_tuple[0]}:{peer_tuple[1]}" if peer_tuple else "unknown"
    conn_id = f"{int(time.time() * 1000) % 100000:05d}"

    try:
        target, headers = await websocket_handshake(reader, writer)
    except Exception as exc:
        logging.warning("[%s] handshake failed from %s: %s", conn_id, peer, exc)
        try:
            await send_http_error(writer, 400, "Bad Request")
        except Exception:
            pass
        return

    parsed = urllib.parse.urlparse(target)
    path = parsed.path or "/"
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    role = "control" if path == "/control" else "worker"
    conn = Connection(
        reader=reader,
        writer=writer,
        peer=peer,
        path=path,
        query=query,
        headers=headers,
        role=role,
        conn_id=conn_id,
    )

    header_secret = maybe_secret_from_headers(headers)
    query_secret = maybe_secret_from_query(query)
    if config.expected_secret and (
        header_secret == config.expected_secret or query_secret == config.expected_secret
    ):
        conn.authenticated = True

    logging.info(
        "[%s] %s connected from %s path=%s query=%s ua=%s",
        conn.conn_id,
        conn.role,
        conn.peer,
        conn.path,
        parsed.query,
        headers.get("user-agent", "-"),
    )

    if config.welcome_json is not None:
        await send_frame(writer, 0x1, json.dumps(config.welcome_json).encode("utf-8"))
    elif config.welcome_text is not None:
        await send_frame(writer, 0x1, config.welcome_text.encode("utf-8"))

    try:
        while True:
            opcode, payload = await read_frame(reader)

            if opcode == 0x8:
                logging.info("[%s] client closed connection", conn.conn_id)
                await send_frame(writer, 0x8, payload[:2] if len(payload) >= 2 else b"")
                break

            if opcode == 0x9:
                await send_frame(writer, 0xA, payload)
                continue

            if opcode == 0xA:
                continue

            if opcode == 0x1:
                text = payload.decode("utf-8", errors="replace")
                logging.info("[%s] text %s", conn.conn_id, text)

                if config.expected_secret and not conn.authenticated:
                    conn.secret_seen_in_message = check_message_secret(text, config.expected_secret)
                    conn.authenticated = conn.secret_seen_in_message
                    if conn.authenticated:
                        logging.info("[%s] authenticated via message payload", conn.conn_id)

                if config.strict_secret and config.expected_secret and not conn.authenticated:
                    logging.warning("[%s] closing unauthenticated connection", conn.conn_id)
                    await send_frame(writer, 0x8, b"")
                    break

                matched = False
                for rule in config.rules:
                    if rule_matches(rule, conn, "text", text):
                        matched = True
                        result = await apply_rule(conn, rule)
                        logging.info("[%s] matched rule path=%s kind=%s", conn.conn_id, rule.path, rule.kind)
                        if result is MAGIC_CLOSE:
                            return

                if config.echo_text and not matched:
                    await send_frame(writer, 0x1, payload)

            elif opcode == 0x2:
                logging.info(
                    "[%s] binary len=%d hex=%s",
                    conn.conn_id,
                    len(payload),
                    preview_binary(payload, config.log_binary_preview),
                )

                matched = False
                for rule in config.rules:
                    if rule_matches(rule, conn, "binary", None):
                        matched = True
                        result = await apply_rule(conn, rule)
                        logging.info("[%s] matched rule path=%s kind=%s", conn.conn_id, rule.path, rule.kind)
                        if result is MAGIC_CLOSE:
                            return

                if config.echo_binary and not matched:
                    await send_frame(writer, 0x2, payload)

            else:
                logging.info("[%s] unsupported opcode=%d", conn.conn_id, opcode)
    except asyncio.IncompleteReadError:
        logging.info("[%s] peer disconnected", conn.conn_id)
    except ConnectionError as exc:
        logging.warning("[%s] websocket protocol error: %s", conn.conn_id, exc)
    except Exception:
        logging.exception("[%s] unexpected error", conn.conn_id)
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        logging.info("[%s] disconnected", conn.conn_id)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local websocket stub server for Cosmog/Joltik rotom endpoints."
    )
    parser.add_argument("--config", help="JSON or TOML server config file")
    parser.add_argument("--bind", help="bind host override")
    parser.add_argument("--port", type=int, help="port override")
    parser.add_argument("--rotom-config", help="existing config.toml to infer host/port/secret")
    parser.add_argument("--secret", help="expected secret override")
    parser.add_argument("--strict-secret", action="store_true", help="close when secret is missing")
    parser.add_argument("--echo-text", action="store_true", help="echo unmatched text frames")
    parser.add_argument("--echo-binary", action="store_true", help="echo unmatched binary frames")
    parser.add_argument("--debug", action="store_true", help="enable debug logging")
    return parser


async def main_async() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = load_server_config(args.config)

    if args.rotom_config:
        host, port = extract_bind_target(args.rotom_config)
        config.host = host
        config.port = port
        if tomllib is not None:
            with open(args.rotom_config, "rb") as f:
                rotom = tomllib.load(f).get("rotom", {})
            if not config.expected_secret:
                config.expected_secret = rotom.get("rotom_secret")

    if args.bind:
        config.host = args.bind
    if args.port:
        config.port = args.port
    if args.secret:
        config.expected_secret = args.secret
    if args.strict_secret:
        config.strict_secret = True
    if args.echo_text:
        config.echo_text = True
    if args.echo_binary:
        config.echo_binary = True

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(message)s")

    server = await asyncio.start_server(
        lambda r, w: handle_connection(r, w, config),
        host=config.host,
        port=config.port,
    )

    for sock in server.sockets or []:
        logging.info("listening on ws://%s:%d and ws://%s:%d/control", sock.getsockname()[0], sock.getsockname()[1], sock.getsockname()[0], sock.getsockname()[1])

    stop_event = asyncio.Event()

    def stop_handler() -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_handler)
        except NotImplementedError:
            pass

    async with server:
        await stop_event.wait()


if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass
