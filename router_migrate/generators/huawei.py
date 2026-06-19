from typing import List
from router_migrate.generators.base import BaseGenerator
from router_migrate.models import MigrationIR, AclRuleIR

class HuaweiGenerator(BaseGenerator):
    def _generate_acl_rule(self, rule: AclRuleIR, seq_num: int) -> str:
        if not rule.action or not rule.protocol:
            return rule.raw_line
        
        parts = [f"rule {seq_num}", rule.action, rule.protocol]
        
        if rule.source == "any":
            parts.append("source any")
        elif rule.source:
            parts.append(f"source {rule.source}")
            
        if rule.source_port:
            parts.append(f"source-port {rule.source_port}")
            
        if rule.destination == "any":
            parts.append("destination any")
        elif rule.destination:
            parts.append(f"destination {rule.destination}")
            
        if rule.destination_port:
            parts.append(f"destination-port {rule.destination_port}")
            
        if rule.log:
            parts.append("logging")
            
        return " ".join(parts)

    def generate(self, migration_ir: MigrationIR) -> str:
        out: List[str] = []
        
        out.append("#")
        out.append("# HUAWEI MIGRATION CONFIG EXTRACT")
        out.append(f"# Source Vendor: {migration_ir.source_vendor}")
        out.append("#")

        # VRFs
        if migration_ir.vrfs:
            out.append("# SECTION: VPN INSTANCES")
            for vrf in migration_ir.vrfs:
                out.append(f"ip vpn-instance {vrf.name}")
                out.append(" ipv4-family")
                if vrf.rd:
                    out.append(f"  route-distinguisher {vrf.rd}")
                for rt in vrf.rt_import:
                    out.append(f"  vpn-target {rt} import-extcommunity")
                for rt in vrf.rt_export:
                    out.append(f"  vpn-target {rt} export-extcommunity")
            out.append("#")

        # VLANs
        if migration_ir.vlans:
            out.append("# SECTION: VLAN DEFINITIONS")
            for vlan in migration_ir.vlans:
                out.append(f"vlan {vlan.vlan_id}")
                if vlan.name:
                    out.append(f" name {vlan.name}")
            out.append("#")

        # Interfaces
        if migration_ir.interfaces:
            out.append("# SECTION: INTERFACES")
            for iface in migration_ir.interfaces:
                out.append(f"interface {iface.name}")
                if iface.description:
                    out.append(f" description {iface.description}")
                if iface.vrf:
                    out.append(f" ip binding vpn-instance {iface.vrf}")
                for ip in iface.ip_addresses:
                    out.append(f" ip address {ip.address} {ip.mask}")
                if iface.acl_in:
                    out.append(f" traffic-filter inbound acl {iface.acl_in}")
                if iface.acl_out:
                    out.append(f" traffic-filter outbound acl {iface.acl_out}")
                if not iface.enabled:
                    out.append(" shutdown")
                else:
                    out.append(" undo shutdown")
            out.append("#")

        # ACLs
        if migration_ir.acls:
            out.append("# SECTION: ACCESS LISTS")
            for acl in migration_ir.acls:
                if acl.name.isdigit():
                    out.append(f"acl number {acl.name}")
                else:
                    out.append(f"acl name {acl.name} advance")
                    
                seq = 5
                for rule in acl.rules:
                    out.append(f" {self._generate_acl_rule(rule, seq)}")
                    seq += 5
            out.append("#")

        # Static Routes
        if migration_ir.static_routes:
            out.append("# SECTION: STATIC ROUTES")
            for sr in migration_ir.static_routes:
                out.append(sr.raw_line.replace("ip route ", "ip route-static "))
            out.append("#")

        # BGP
        if migration_ir.bgp_vrfs:
            out.append("# SECTION: BGP VRF STANZAS")
            out.append("bgp <ASN_PLACEHOLDER>")
            for bgp in migration_ir.bgp_vrfs:
                out.append(f" ipv4-family vpn-instance {bgp.vrf}")
                for line in bgp.raw_lines:
                    line = line.strip()
                    if line.startswith("neighbor"):
                        # neighbor to peer translation
                        peer_line = line.replace("neighbor", "peer")
                        out.append(f"  {peer_line}")
            out.append("#")

        if migration_ir.warnings:
            out.append("# WARNINGS:")
            for w in migration_ir.warnings:
                out.append(f"# [WARN] {w}")

        return "\n".join(out)
