import re
from typing import List, Dict
from router_migrate.parsers.base import BaseParser
from router_migrate.models import DeviceIR, InterfaceIR, VrfIR, VlanIR, AclIR, AclRuleIR, BgpVrfIR, BgpNeighborIR, StaticRouteIR, RouteMapIR, RouteMapRuleIR, IPAddress

class HuaweiParser(BaseParser):
    def _split_blocks(self, text: str) -> List[List[str]]:
        blocks = []
        current_block = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                # Huawei often uses '#' to delimit blocks or comment
                if stripped == "#":
                    if current_block:
                        blocks.append(current_block)
                        current_block = []
                continue
            
            # If not using '#' strictly, Huawei still groups by indentation or no indentation
            # For simplicity, we just aggregate if it starts with space, or handle specific headers
            if line.startswith(" ") or line.startswith("\t"):
                current_block.append(stripped)
            else:
                if current_block:
                    blocks.append(current_block)
                current_block = [stripped]
        if current_block:
            blocks.append(current_block)
        return blocks

    def _parse_acl_rule(self, raw_line: str) -> AclRuleIR:
        # Huawei rule: rule 5 permit ip source 10.0.0.1 0 destination any
        rule = AclRuleIR(action="permit", protocol="ip", source="any", destination="any", raw_line=raw_line)
        parts = raw_line.split()
        if not parts: return rule
        
        if parts[0] == "rule":
            parts.pop(0)
        if parts and parts[0].isdigit():
            parts.pop(0) # pop seq
            
        if not parts: return rule
        rule.action = parts.pop(0)
        
        if not parts: return rule
        rule.protocol = parts.pop(0)
        
        # very simplified source/dest parsing for Huawei
        if "source" in parts:
            idx = parts.index("source")
            if len(parts) > idx + 1:
                if parts[idx+1] == "any":
                    rule.source = "any"
                else:
                    # ip wildcard
                    if len(parts) > idx + 2:
                        rule.source = f"{parts[idx+1]} {parts[idx+2]}"
        
        if "destination" in parts:
            idx = parts.index("destination")
            if len(parts) > idx + 1:
                if parts[idx+1] == "any":
                    rule.destination = "any"
                else:
                    if len(parts) > idx + 2:
                        rule.destination = f"{parts[idx+1]} {parts[idx+2]}"
        
        if "logging" in parts:
            rule.log = True
            
        return rule

    def parse(self, config_text: str) -> DeviceIR:
        ir = DeviceIR()
        blocks = self._split_blocks(config_text)
        
        for block in blocks:
            header = block[0]
            
            # Interface
            if header.startswith("interface "):
                iface_name = header.split("interface ")[1].strip()
                iface = InterfaceIR(name=iface_name, raw_lines=block)
                for line in block[1:]:
                    if line.startswith("description"):
                        iface.description = line.replace("description", "").strip()
                    elif line.startswith("ip binding vpn-instance"):
                        iface.vrf = line.replace("ip binding vpn-instance", "").strip()
                    elif line.startswith("ip address"):
                        parts = line.split()
                        if len(parts) >= 3:
                            iface.ip_addresses.append(IPAddress(address=parts[2], mask=parts[3] if len(parts)>3 else "24"))
                    elif line.startswith("traffic-filter"):
                        parts = line.split()
                        if len(parts) >= 3:
                            direction = parts[1] # inbound or outbound
                            acl_name = parts[3] if parts[2] == "acl" else parts[2]
                            if direction == "inbound":
                                iface.acl_in = acl_name
                            else:
                                iface.acl_out = acl_name
                    elif line == "shutdown":
                        iface.enabled = False
                    elif line == "undo shutdown":
                        iface.enabled = True
                ir.interfaces[iface_name] = iface

            # VRF (VPN-Instance)
            elif header.startswith("ip vpn-instance "):
                vrf_name = header.replace("ip vpn-instance ", "").strip()
                vrf = VrfIR(name=vrf_name, raw_lines=block)
                for line in block[1:]:
                    if line.startswith("route-distinguisher "):
                        vrf.rd = line.replace("route-distinguisher ", "").strip()
                    elif line.startswith("vpn-target"):
                        # vpn-target 1:1 import-extcommunity
                        parts = line.split()
                        if len(parts) >= 3:
                            rt = parts[1]
                            dir_type = parts[2]
                            if "import" in dir_type:
                                vrf.rt_import.append(rt)
                            elif "export" in dir_type:
                                vrf.rt_export.append(rt)
                            elif "both" in dir_type:
                                vrf.rt_import.append(rt)
                                vrf.rt_export.append(rt)
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
            elif header.startswith("acl number") or header.startswith("acl name"):
                parts = header.split()
                name = parts[-1]
                acl = AclIR(name=name, type="extended", raw_lines=block)
                for line in block[1:]:
                    if line.startswith("rule "):
                        acl.rules.append(self._parse_acl_rule(line))
                ir.acls[name] = acl

            # BGP
            elif header.startswith("bgp "):
                current_vrf = None
                for line in block[1:]:
                    if line.startswith("ipv4-family vpn-instance "):
                        current_vrf = line.replace("ipv4-family vpn-instance ", "").strip()
                        if current_vrf not in ir.bgp_vrfs:
                            ir.bgp_vrfs[current_vrf] = BgpVrfIR(vrf=current_vrf, raw_lines=[])
                    elif current_vrf:
                        ir.bgp_vrfs[current_vrf].raw_lines.append(line)
                        if line.startswith("peer"):
                            parts = line.split()
                            if len(parts) >= 2:
                                ip = parts[1]
                                if ip not in ir.bgp_vrfs[current_vrf].neighbors:
                                    ir.bgp_vrfs[current_vrf].neighbors[ip] = BgpNeighborIR(ip=ip, raw_lines=[])

        # Static Routes
        for line in config_text.splitlines():
            line = line.strip()
            if line.startswith("ip route-static "):
                ir.static_routes.append(StaticRouteIR(prefix="", next_hop="", raw_line=line))

        return ir

    def parse_snippet(self, snippet_text: str) -> DeviceIR:
        return self.parse(snippet_text)
