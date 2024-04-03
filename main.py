import dataclasses
import typing
import libknot.control
import app
import time
import requests

flask_app = app.create_app()


@dataclasses.dataclass
class DNSEntry:
    id: int
    label: str
    ipv4: str
    ipv6: str


@flask_app.route("/webhook", methods=["POST"])
def webhook():
    records = get_table_data()
    make_zone_file(records)
    update_knot()

    return ""


def get_table_data():
    r = requests.get(
        f"{flask_app.config['GRIST_BASE_URL']}/api/docs/{flask_app.config['GRIST_DOCUMENT_ID']}"
        f"/tables/{flask_app.config['GRIST_TABLE_ID']}/records",
        headers={
            "Authorization": f"Bearer {flask_app.config['GRIST_API_KEY']}",
            "Accept": "application/json",
        }
    )
    r.raise_for_status()

    records = list(map(lambda record: DNSEntry(
        id=record["id"],
        label=record["fields"]["DNS_Label"],
        ipv4=record["fields"]["IPv4_Address"].strip().removesuffix(".") if record["fields"]["IPv4_Address"] else None,
        ipv6=record["fields"]["IPv6_Address"].strip().removesuffix(".") if record["fields"]["IPv6_Address"] else None,
    ), r.json()["records"]))
    return records


def make_zone_file(records: typing.List[DNSEntry]):
    with open(flask_app.config["ZONE_FILE_LOCATION"], "w") as f:
        f.write(f"$TTL 3600\n")
        f.write(f"@ IN SOA ns.example.com. noc.emfcamp.org. (\n")
        f.write(f"  {int(time.time())} ; Serial\n")
        f.write(f"  3600 ; Refresh\n")
        f.write(f"  1800 ; Retry\n")
        f.write(f"  604800 ; Expire\n")
        f.write(f"  3600 ; Negative Cache TTL\n")
        f.write(f")\n")
        f.write(f"\n")
        f.write(f"@ IN NS ns.example.com.\n")
        f.write(f"\n")

        for record in records:
            f.write(f"; Record #{record.id}\n")
            if record.ipv4:
                f.write(f"{record.label}.at.emf.camp. IN A {record.ipv4}\n")
            if record.ipv6:
                f.write(f"{record.label}.at.emf.camp. IN AAAA {record.ipv6}\n")
            f.write(f"\n")


def update_knot():
    ctl = libknot.control.KnotCtl()
    ctl.connect(flask_app.config["KNOT_SOCKET_LOCATION"])

    try:
        ctl.send_block(cmd="zone-reload", zone="at.emf.camp")
        ctl.receive_block()
    finally:
        try:
            ctl.send(libknot.control.KnotCtlType.END)
            ctl.close()
        except libknot.control.KnotCtlError:
            pass
