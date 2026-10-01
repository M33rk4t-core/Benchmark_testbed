# Local evaluation services

Seven local web applications for static review, DOM capture, and input-sink scoring. Each application lives in `targets/<name>/` and carries its own `spec.json`. That file is the ground truth for how each parameter is handled: raw passthrough, a state change with no authorization check, or a bounded control.

| Service | Stack | Port | Scored route |
| --- | --- | --- | --- |
| Fieldnote | WordPress | 8081 | `/catalog` |
| Ashford Registry | WordPress | 8082 | `/directory` |
| Lumen Floor | WordPress | 8083 | `/console` |
| Waybill Desk | FastAPI | 8084 | `/track` |
| Halden Seminar | Express | 8085 | `/apply` |
| Stockwell Register | Flask | 8086 | `/holdings` |
| Vellum Room | Node | 8087 | `/reading-room` |

## Start

Docker is required.

```powershell
.\setup.ps1
```

```bash
./setup.sh
```

The script builds the containers, installs the three WordPress sites, and writes frozen HTML into `snapshots/`. WordPress desk login for the local sites is `archivist` / `local-archivist`. Database user `bench` uses password `bench-local-only` and is reachable only on the compose network.

MySQL initializes `init-db.sql` only when the data volume is first created. To seed again, remove that volume:

```bash
docker compose down -v
```

## Scoring files

Read `targets/<name>/spec.json`. `scheme` is one of:

- `raw_passthrough` — the value reaches the named sink without encoding, binding, or an allowlist
- `missing_authorization` — the value is stored without a role or capability check
- `bounded_control` — a type constraint, allowlist, nonce, encoding, or bound query limits the value

`other_uses` records a second, encoded appearance of the same parameter, such as a form field.
