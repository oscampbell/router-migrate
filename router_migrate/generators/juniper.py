from typing import List
from router_migrate.generators.base import BaseGenerator
from router_migrate.models import MigrationIR, AclRuleIR

class JuniperGenerator(BaseGenerator):
    def generate(self, migration_ir: MigrationIR) -> str:
        out: List[str] = []
        
        out.append("!" + "=" * 68)
        out.append("! JUNIPER MIGRATION CONFIG EXTRACT (SET FORMAT)")
        out.append(f"! Source Vendor: {migration_ir.source_vendor}")
        out.append("!" + "=" * 68)
        out.append("")

        # VRFs
        if migration_ir.vrfs:
            out.append("! SECTION: VRF DEFINITIONS")
            out.append("!" + "-" * 68)
            for vrf in migration_ir.vrfs:
                out.append(f"set routing-instances {vrf.name} instance-type vrf")
                if vrf.rd:
                    out.append(f"set routing-instances {vrf.name} route-distinguisher {vrf.rd}")
                for rt in vrf.rt_import:
                    out.append(f"set routing-instances {vrf.name} vrf-target import {rt}")
                for rt in vrf.rt_export:
                    out.append(f"set routing-instances {vrf.name} vrf-target export {rt}")
            out.append("")

        # VLANs
        if migration_ir.vlans:
            out.append("! SECTION: VLAN DEFINITIONS")
            out.append("!" + "-" * 68)
            for vlan in migration_ir.vlans:
                name = vlan.name if vlan.name else f"VLAN{vlan.vlan_id}"
                out.append(f"set vlans {name} vlan-id {vlan.vlan_id}")
            out.append("")

        # Interfaces
        if migration_ir.interfaces:
            out.append("! SECTION: INTERFACES")
            out.append("!" + "-" * 68)
            for iface in migration_ir.interfaces:
                # Juniper uses ge-0/0/0, etc. We don't magically translate interface naming here
                # unless a rename map is used in migrator, which cli.py supports.
                out.append(f"set interfaces {iface.name} description \"{iface.description or ''}\"")
                if not iface.enabled:
                    out.append(f"set interfaces {iface.name} disable")
                
                if iface.vrf:
                    out.append(f"set routing-instances {iface.vrf} interface {iface.name}.0")
                    
                for ip in iface.ip_addresses:
                    out.append(f"set interfaces {iface.name} unit 0 family inet address {ip.address}/{ip.mask}")
                
                if iface.acl_in:
                    out.append(f"set interfaces {iface.name} unit 0 family inet filter input {iface.acl_in}")
                if iface.acl_out:
                    out.append(f"set interfaces {iface.name} unit 0 family inet filter output {iface.acl_out}")
            out.append("")

        # ACLs
        if migration_ir.acls:
            out.append("! SECTION: ACCESS LISTS")
            out.append("!" + "-" * 68)
            for acl in migration_ir.acls:
                # We construct term 1, 2, 3...
                term_id = 10
                for rule in acl.rules:
                    base_cmd = f"set firewall family inet filter {acl.name} term {term_id}"
                    
                    if rule.protocol and rule.protocol != "ip":
                        out.append(f"{base_cmd} from protocol {rule.protocol}")
                    
                    if rule.source and rule.source != "any":
                        if rule.source.startswith("host"):
                            ip = rule.source.split()[1]
                            out.append(f"{base_cmd} from source-address {ip}/32")
                        else:
                            parts = rule.source.split()
                            if len(parts) == 2: # ip mask
                                # convert mask to prefix len is complex without ipaddress module, we'll write raw
                                out.append(f"{base_cmd} from source-address {parts[0]}") # mask ignored for now
                            else:
                                out.append(f"{base_cmd} from source-address {rule.source}")
                    
                    if rule.destination and rule.destination != "any":
                        if rule.destination.startswith("host"):
                            ip = rule.destination.split()[1]
                            out.append(f"{base_cmd} from destination-address {ip}/32")
                        else:
                            parts = rule.destination.split()
                            if len(parts) == 2:
                                out.append(f"{base_cmd} from destination-address {parts[0]}")
                            else:
                                out.append(f"{base_cmd} from destination-address {rule.destination}")
                                
                    if rule.source_port:
                        out.append(f"{base_cmd} from source-port {rule.source_port.replace('eq ', '')}")
                    if rule.destination_port:
                        out.append(f"{base_cmd} from destination-port {rule.destination_port.replace('eq ', '')}")
                        
                    action = "accept" if rule.action == "permit" else "discard"
                    out.append(f"{base_cmd} then {action}")
                    
                    if rule.log:
                        out.append(f"{base_cmd} then log")
                        
                    term_id += 10
            out.append("")

        # Static Routes
        if migration_ir.static_routes:
            out.append("! SECTION: STATIC ROUTES")
            out.append("!" + "-" * 68)
            for sr in migration_ir.static_routes:
                # We assume next-hop is available in raw_line for now, but use prefix
                pass # need better static route extraction for universal, using raw for now
                out.append(f"! {sr.raw_line}")
            out.append("")

        if migration_ir.warnings:
            out.append("! WARNINGS:")
            for w in migration_ir.warnings:
                out.append(f"! [WARN] {w}")

        return "\n".join(out)
