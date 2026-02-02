import requests
import pandas as pd
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========================
# CONFIGURAÇÕES
# ========================
ZABBIX_URL = "https://10.115.0.199/api_jsonrpc.php"
API_TOKEN = "SUA API"
GROUP_NAME = "GRUPO ONDE O HOST VAI SER ADICIONADO"
CSV_FILE = "AQUIVO ONDE ESTÁ OS HOSTS .csv"

HEADERS = {
    "Content-Type": "application/json-rpc"
}

# ========================
# FUNÇÃO GENÉRICA ZABBIX
# ========================
def zabbix_api(method, params):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "auth": API_TOKEN,
        "id": 1
    }

    response = requests.post(
        ZABBIX_URL,
        headers=HEADERS,
        json=payload,
        verify=False
    )

    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise Exception(data["error"])

    return data["result"]

# ========================
# FUNÇÕES ZABBIX
# Na tabela o nome da coluna deve ser "hostname"
# ========================
def get_group_id():
    result = zabbix_api(
        "hostgroup.get",
        {
            "filter": {
                "name": [GROUP_NAME]
            }
        }
    )

    if not result:
        raise Exception(f"Grupo '{GROUP_NAME}' não encontrado")

    return result[0]["groupid"]

def get_host(hostname):
    return zabbix_api(
        "host.get",
        {
            "filter": {
                "host": [hostname]
            },
            "selectGroups": ["groupid"]
        }
    )

def add_group_to_host(host, group_id):
    groups = [{"groupid": g["groupid"]} for g in host["groups"]]

    if {"groupid": group_id} in groups:
        print(f"[INFO] {host['host']} já está no grupo {GROUP_NAME}")
        return

    groups.append({"groupid": group_id})

    zabbix_api(
        "host.update",
        {
            "hostid": host["hostid"],
            "groups": groups
        }
    )

    print(f"[OK] {host['host']} adicionado ao grupo {GROUP_NAME}")

# ========================
# EXECUÇÃO
# ========================
def main():
    print("=== INICIANDO PROCESSO ZABBIX ===")

    group_id = get_group_id()
    print(f"[OK] Grupo '{GROUP_NAME}' -> ID {group_id}")

    df = pd.read_csv(CSV_FILE)

    for _, row in df.iterrows():
        hostname = row["hostname"]

        hosts = get_host(hostname)

        if not hosts:
            print(f"[ERRO] Host '{hostname}' não encontrado no Zabbix")
            continue

        add_group_to_host(hosts[0], group_id)

    print("=== PROCESSO FINALIZADO ===")

if __name__ == "__main__":
    main()
