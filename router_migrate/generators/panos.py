from typing import List
from router_migrate.generators.base import BaseGenerator
from router_migrate.models import MigrationIR

class PanosGenerator(BaseGenerator):
    def generate(self, migration_ir: MigrationIR) -> str:
        out: List[str] = []
        
        out.append("# ====================================================================")
        out.append("# PALO ALTO (PAN-OS) MIGRATION CONFIG EXTRACT")
        out.append(f"# Source Vendor: {migration_ir.source_vendor}")
        out.append("# ====================================================================")
        out.append("")

        if migration_ir.interfaces:
            for iface in migration_ir.interfaces:
                out.append(f"set network interface ethernet {iface.name} layer3")
                if iface.description:
                    out.append(f"set network interface ethernet {iface.name} layer3 comment \"{iface.description}\"")
                for ip in iface.ip_addresses:
                    out.append(f"set network interface ethernet {iface.name} layer3 ip {ip.address}/{ip.mask}")
                if iface.mtu:
                    out.append(f"set network interface ethernet {iface.name} layer3 mtu {iface.mtu}")
            out.append("")

        return "\n".join(out)
