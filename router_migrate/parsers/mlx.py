import re
from typing import List, Dict
from router_migrate.parsers.base import BaseParser
from router_migrate.models import DeviceIR, InterfaceIR, VrfIR, VlanIR, AclIR, AclRuleIR, BgpVrfIR, BgpNeighborIR, StaticRouteIR, RouteMapIR, RouteMapRuleIR, IPAddress

class MlxParser(BaseParser):
    def _split_blocks(self, text: str) -> List[List[str]]:
        blocks = []
        current_block = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("!"):
                continue
            if line.startswith(" "):
                current_block.append(stripped)
            else:
                if current_block:
                    blocks.append(current_block)
                current_block = [stripped]
        if current_block:
            blocks.append(current_block)
        return blocks

    def _parse_acl_rule(self, raw_line: str) -> AclRuleIR:
        # remove 'access-list XXX ' if present
        if "access-list" in raw_line:
            parts = raw_line.split("access-list ", 1)[1].split(maxsplit=1)
            if len(parts) > 1:
                raw_line = parts[1]

        rule = AclRuleIR(action="permit", protocol="ip", source="any", destination="any", raw_line=raw_line)
        parts = raw_line.split()
        if not parts: return rule
        
        if parts[0].isdigit():
            parts.pop(0)
            
        if not parts: return rule
        rule.action = parts.pop(0)
        
        if not parts: return rule
        rule.protocol = parts.pop(0)
        
        if not parts: return rule
        if parts[0] == "any":
            rule.source = "any"
            parts.pop(0)
        elif parts[0] == "host":
            parts.pop(0)
            rule.source = f"host {parts.pop(0)}" if parts else "any"
        else:
            ip = parts.pop(0)
            mask = parts.pop(0) if parts else "0.0.0.0"
            rule.source = f"{ip} {mask}"
            
        if parts and parts[0] in ["eq", "gt", "lt", "neq", "range"]:
            op = parts.pop(0)
            port = parts.pop(0)
            if op == "range":
                port2 = parts.pop(0) if parts else ""
                rule.source_port = f"{op} {port} {port2}".strip()
            else:
                rule.source_port = f"{op} {port}"

        if not parts: return rule
        if parts[0] == "any":
            rule.destination = "any"
            parts.pop(0)
        elif parts[0] == "host":
            parts.pop(0)
            rule.destination = f"host {parts.pop(0)}" if parts else "any"
        else:
            ip = parts.pop(0)
            mask = parts.pop(0) if parts else "0.0.0.0"
            rule.destination = f"{ip} {mask}"
            
        if parts and parts[0] in ["eq", "gt", "lt", "neq", "range"]:
            op = parts.pop(0)
            port = parts.pop(0)
            if op == "range":
                port2 = parts.pop(0) if parts else ""
                rule.destination_port = f"{op} {port} {port2}".strip()
            else:
                rule.destination_port = f"{op} {port}"
                
        if "log" in parts:
            rule.log = True
            
        return rule

    def parse(self, config_text: str) -> DeviceIR:
        ir = DeviceIR()
        blocks = self._split_blocks(config_text)
        
        # We need to process line by line for some global items
        # Let's iterate through blocks
        for block in blocks:
            header = block[0]
            
            # Interface
            if header.startswith("interface "):
                iface_name = header.split("interface ")[1].strip()
                iface = InterfaceIR(name=iface_name, raw_lines=block)
                for line in block[1:]:
                    if line.startswith("port-name"):
                        iface.description = line.replace("port-name", "").strip()
                    elif line.startswith("vrf forwarding"):
                        iface.vrf = line.replace("vrf forwarding", "").strip()
                    elif line.startswith("ip address"):
                        parts = line.split()
                        if len(parts) >= 3:
                            # MLX format is usually `ip address 10.0.0.1/24` or `ip address 10.0.0.1 255.255.255.0`
                            if "/" in parts[2]:
                                addr, mask = parts[2].split("/")
                                iface.ip_addresses.append(IPAddress(address=addr, mask=mask))
                            elif len(parts) >= 4:
                                iface.ip_addresses.append(IPAddress(address=parts[2], mask=parts[3]))
                    elif line.startswith("ip access-group"):
                        # ip access-group ACL_NAME in|out
                        parts = line.split()
                        if len(parts) >= 4:
                            acl_name = parts[2]
                            direction = parts[3]
                            if direction == "in":
                                iface.acl_in = acl_name
                            else:
                                iface.acl_out = acl_name
                    elif line == "disable":
                        iface.enabled = False
                    elif line.startswith("vlan-config"):
                        # simplified vlan extraction
                        pass
                ir.interfaces[iface_name] = iface

            # VRF
            elif header.startswith("vrf "):
                vrf_name = header.split("vrf ")[1].strip()
                vrf = VrfIR(name=vrf_name, raw_lines=block)
                for line in block[1:]:
                    if line.startswith("rd "):
                        vrf.rd = line.replace("rd ", "").strip()
                    elif line.startswith("route-target export"):
                        vrf.rt_export.append(line.replace("route-target export ", "").strip())
                    elif line.startswith("route-target import"):
                        vrf.rt_import.append(line.replace("route-target import ", "").strip())
                    elif line.startswith("route-target both"):
                        rt = line.replace("route-target both ", "").strip()
                        vrf.rt_export.append(rt)
                        vrf.rt_import.append(rt)
                ir.vrfs[vrf_name] = vrf

            # VLAN
            elif header.startswith("vlan "):
                parts = header.split()
                if len(parts) >= 2:
                    vlan_id = parts[1]
                    vlan = VlanIR(vlan_id=vlan_id, raw_lines=block)
                    for line in block[1:]:
                        if line.startswith("name "):
                            vlan.name = line.replace("name ", "").strip()
                    ir.vlans[vlan_id] = vlan

            # ACL
            elif header.startswith("access-list") or header.startswith("ip access-list"):
                # MLX syntax: ip access-list extended NAME or access-list NUMBER permit ...
                if "access-list" in header:
                    parts = header.split()
                    if "extended" in parts or "standard" in parts:
                        name = parts[-1]
                        acl = AclIR(name=name, type="extended" if "extended" in parts else "standard", raw_lines=block)
                        for line in block[1:]:
                            if line.startswith("permit") or line.startswith("deny") or (line.split()[0].isdigit() and (line.split()[1] == "permit" or line.split()[1] == "deny")):
                                acl.rules.append(self._parse_acl_rule(line))
                        ir.acls[name] = acl
                    else:
                        # numbered ACL
                        # access-list 100 permit ip any any
                        num = parts[1]
                        if num not in ir.acls:
                            ir.acls[num] = AclIR(name=num, type="numbered", raw_lines=[])
                        ir.acls[num].raw_lines.append(header)
                        ir.acls[num].rules.append(self._parse_acl_rule(header))

            # BGP (simplified, MLX BGP config is global then vrf based)
            elif header.startswith("router bgp"):
                # in MLX, address-family ipv4 unicast vrf NAME inside router bgp
                current_vrf = None
                for line in block[1:]:
                    if line.startswith("address-family ipv4 unicast vrf"):
                        current_vrf = line.split("vrf ")[-1].strip()
                        if current_vrf not in ir.bgp_vrfs:
                            ir.bgp_vrfs[current_vrf] = BgpVrfIR(vrf=current_vrf, raw_lines=[])
                    elif current_vrf:
                        ir.bgp_vrfs[current_vrf].raw_lines.append(line)
                        if line.startswith("neighbor"):
                            # Simple extraction
                            parts = line.split()
                            if len(parts) >= 2:
                                ip = parts[1]
                                if ip not in ir.bgp_vrfs[current_vrf].neighbors:
                                    ir.bgp_vrfs[current_vrf].neighbors[ip] = BgpNeighborIR(ip=ip, raw_lines=[])
                                if "route-map" in line:
                                    rm_index = parts.index("route-map")
                                    if len(parts) > rm_index + 2:
                                        direction = parts[rm_index + 1]
                                        rm_name = parts[rm_index + 2]
                                        if direction == "in":
                                            ir.bgp_vrfs[current_vrf].neighbors[ip].route_map_in = rm_name
                                        elif direction == "out":
                                            ir.bgp_vrfs[current_vrf].neighbors[ip].route_map_out = rm_name

            # Route Map
            elif header.startswith("route-map"):
                parts = header.split()
                if len(parts) >= 3:
                    name = parts[1]
                    seq = int(parts[-1]) if parts[-1].isdigit() else 10
                    action = parts[2] # permit or deny
                    if name not in ir.route_maps:
                        ir.route_maps[name] = RouteMapIR(name=name, raw_lines=[])
                    
                    rm_rule = RouteMapRuleIR(action=action, sequence=seq, raw_lines=block)
                    for line in block[1:]:
                        if line.startswith("match"):
                            rm_rule.match_clauses.append(line)
                        elif line.startswith("set"):
                            rm_rule.set_clauses.append(line)
                    ir.route_maps[name].rules.append(rm_rule)
                    ir.route_maps[name].raw_lines.extend(block)
        
        # Static Routes
        for line in config_text.splitlines():
            line = line.strip()
            if line.startswith("ip route "):
                # ip route 10.0.0.0/8 1.2.3.4
                ir.static_routes.append(StaticRouteIR(prefix="", next_hop="", raw_line=line))

        return ir

    def parse_snippet(self, snippet_text: str) -> DeviceIR:
        # A snippet can just be parsed as a full config
        return self.parse(snippet_text)
