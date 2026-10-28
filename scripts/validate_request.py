
import ipaddress
import json
import os
import sys
import tomllib
import urllib.parse
import urllib.request
from pathlib import Path

# La ruta recibida debe apuntar a un TOML dentro de requests/.
request_path = Path(sys.argv[1])

if request_path.is_absolute() or ".." in request_path.parts:
    raise SystemExit("Ruta de solicitud no permitida")

if len(request_path.parts) != 2 or request_path.parts[0] != "requests":
    raise SystemExit("Usa una ruta como requests/vm-dev-01.toml")

if request_path.suffix != ".toml":
    raise SystemExit("La solicitud debe ser un archivo TOML")

repo_root = Path.cwd().resolve()
request_file = (repo_root / request_path).resolve()

if not request_file.is_relative_to((repo_root / "requests").resolve()):
    raise SystemExit("Ruta fuera del directorio requests")

with request_file.open("rb") as f:
    request = tomllib.load(f)

required = {
    "request": ["request_id", "name", "environment", "resource_type"],
    "compute": ["instance_type", "operating_system"],
    "network": ["site", "prefix"],
}

for section, fields in required.items():
    if not isinstance(request.get(section), dict):
        raise SystemExit(f"Falta la sección [{section}]")
    for field in fields:
        if not isinstance(request[section].get(field), str) or not request[section][field].strip():
            raise SystemExit(f"Falta {section}.{field}")

network = request["network"]
prefix = ipaddress.ip_network(network["prefix"], strict=True)

base_url = os.environ.get(
    "NETBOX_URL", "http://localhost:8000"
).rstrip("/")
token = os.environ.get("NETBOX_TOKEN", "")
scheme = os.environ.get("NETBOX_AUTH_SCHEME", "Bearer")

if not token:
    raise SystemExit("Falta configurar NETBOX_TOKEN")

def get_json(path_or_url):
    url = (
        path_or_url
        if path_or_url.startswith(("http://", "https://"))
        else f"{base_url}/{path_or_url.lstrip('/')}"
    )

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"{scheme} {token}",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)

def list_all(path):
    results = []
    url = f"{base_url}/{path.lstrip('/')}"

    while url:
        page = get_json(url)
        results.extend(page.get("results", []))
        url = page.get("next")

    return results

# Verificar que existe exactamente un sitio con ese nombre.
site_query = urllib.parse.urlencode({"name": network["site"]})
sites = get_json(f"/api/dcim/sites/?{site_query}")["results"]
sites = [s for s in sites if s.get("name") == network["site"]]

if len(sites) != 1:
    raise SystemExit(
        f"Se esperaba un sitio {network['site']}; encontrados: {len(sites)}"
    )

# Consultar el prefijo exacto.
prefix_query = urllib.parse.urlencode({"prefix": str(prefix)})
prefixes = get_json(f"/api/ipam/prefixes/?{prefix_query}")["results"]
prefixes = [p for p in prefixes if p.get("prefix") == str(prefix)]

if len(prefixes) != 1:
    raise SystemExit(
        f"Se esperaba un prefijo {prefix}; encontrados: {len(prefixes)}"
    )

# Consultar las IP registradas. Esta operación es de solo lectura.
addresses = list_all("/api/ipam/ip-addresses/?limit=1000")
used = set()

for item in addresses:
    try:
        ip = ipaddress.ip_interface(item["address"]).ip
        if ip.version == prefix.version and ip in prefix:
            used.add(ip)
    except (ValueError, KeyError, TypeError):
        continue

candidate = next(
    (ip for ip in prefix.hosts() if ip not in used),
    None,
)

if candidate is None:
    raise SystemExit(f"No hay IP candidata libre en {prefix}")

result = {
    "request_id": request["request"]["request_id"],
    "vm_name": request["request"]["name"],
    "environment": request["request"]["environment"],
    "site": sites[0]["name"],
    "prefix": prefixes[0]["prefix"],
    "prefix_id": prefixes[0]["id"],
    "ip_candidate": str(candidate),
    "ip_candidate_reserved": False,
    "registered_ips_in_prefix": len(used),
}

# Guardar exclusivamente el objeto JSON en el archivo.
output_file = Path.cwd() / "netbox-result.json"
output_file.write_text(
    json.dumps(result, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

# Estos mensajes se muestran en los logs, no dentro del archivo.
print(f"IP candidata de NetBox: {candidate}", flush=True)
print(f"Resultado guardado en {output_file}", flush=True)
print("=== RESULTADO DE NETBOX ===", flush=True)
print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)
