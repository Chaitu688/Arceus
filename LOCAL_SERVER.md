# Local Rotom Server

This repository contains a stripped Android client bundle. `local_server.py` provides a minimal local websocket backend with the same network shape the client expects:

- `ws://HOST:PORT/` for worker traffic
- `ws://HOST:PORT/control` for device/control traffic

It is intentionally permissive because the original backend protocol is not present in this repository.

## Start it against an existing config

```bash
python3 local_server.py --rotom-config /home/chaitu/joltik-master/config.toml --debug
```

That reads:

- `rotom_worker_endpoint` to infer bind host and port
- `rotom_secret` to optionally detect/authenticate messages containing the shared secret

## Start it with a custom stub config

```bash
python3 local_server.py --config local_server.example.json --debug
```

## Useful flags

```bash
python3 local_server.py --bind 0.0.0.0 --port 7070 --echo-text --echo-binary --debug
python3 local_server.py --rotom-config /home/chaitu/joltik-master/config.toml --strict-secret
```

## What it does

- Accepts websocket upgrade requests on `/` and `/control`
- Logs text frames and binary frame previews
- Auto-replies to websocket ping frames
- Optionally echoes unmatched text or binary frames
- Can match simple rules and send canned JSON, text, or binary responses

## Limits

- No TLS
- No fragmented websocket frames
- No knowledge of the real proprietary payload schema

Use it to capture the client’s first messages, then extend the rule set based on observed traffic.
