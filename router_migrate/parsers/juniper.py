from typing import List, Dict
from router_migrate.parsers.base import BaseParser
from router_migrate.models import DeviceIR, InterfaceIR, VrfIR, VlanIR, AclIR, AclRuleIR, BgpVrfIR, BgpNeighborIR, StaticRouteIR, RouteMapIR, RouteMapRuleIR, IPAddress

class JuniperParser(BaseParser):
    def parse(self, config_text: str) -> DeviceIR:
        ir = DeviceIR()
        
        # We assume flat "set" format for Junos parser
        # e.g., "set interfaces ge-0/0/0 description mydesc"
        for line in config_text.splitlines():
            line = line.strip()
            if not line.startswith("set "):
                continue
            
            parts = line.split()
            if len(parts) < 3:
                continue
                
            # Interfaces
            if parts[1] == "interfaces":
                iface_name = parts[2]
                if iface_name not in ir.interfaces:
                    ir.interfaces[iface_name] = InterfaceIR(name=iface_name, raw_lines=[])
                ir.interfaces[iface_name].raw_lines.append(line)
                
                if len(parts) > 3:
                    if parts[3] == "description":
                        ir.interfaces[iface_name].description = " ".join(parts[4:]).strip('"')
                    elif parts[3] == "disable":
                        ir.interfaces[iface_name].enabled = False
                    elif parts[3] == "unit" and len(parts) > 6:
                        if parts[5] == "family" and parts[6] == "inet" and parts[7] == "address":
                            addr_mask = parts[8]
                            if "/" in addr_mask:
                                addr, mask = addr_mask.split("/")
                                ir.interfaces[iface_name].ip_addresses.append(IPAddress(address=addr, mask=mask))
                        elif parts[5] == "family" and parts[6] == "inet" and parts[7] == "filter":
                            direction = parts[8] # input or output
                            acl_name = parts[9]
                            if direction == "input":
                                ir.interfaces[iface_name].acl_in = acl_name
                            else:
                                ir.interfaces[iface_name].acl_out = acl_name

            # Routing instances (VRFs)
            elif parts[1] == "routing-instances":
                vrf_name = parts[2]
                if vrf_name not in ir.vrfs:
                    ir.vrfs[vrf_name] = VrfIR(name=vrf_name, raw_lines=[])
                ir.vrfs[vrf_name].raw_lines.append(line)
                
                if len(parts) > 3:
                    if parts[3] == "route-distinguisher":
                        ir.vrfs[vrf_name].rd = parts[4]
                    elif parts[3] == "vrf-target":
                        if len(parts) > 5 and parts[4] == "import":
                            ir.vrfs[vrf_name].rt_import.append(parts[5])
                        elif len(parts) > 5 and parts[4] == "export":
                            ir.vrfs[vrf_name].rt_export.append(parts[5])
                        else:
                            ir.vrfs[vrf_name].rt_import.append(parts[4])
                            ir.vrfs[vrf_name].rt_export.append(parts[4])
                    elif parts[3] == "interface":
                        iface = parts[4].split('.')[0]
                        if iface in ir.interfaces:
                            ir.interfaces[iface].vrf = vrf_name

            # VLANs
            elif parts[1] == "vlans":
                vlan_name = parts[2]
                # We need to map vlan name to vlan id in junos
                # set vlans VLAN_NAME vlan-id 10
                if len(parts) > 4 and parts[3] == "vlan-id":
                    vlan_id = parts[4]
                    if vlan_id not in ir.vlans:
                        ir.vlans[vlan_id] = VlanIR(vlan_id=vlan_id, name=vlan_name, raw_lines=[])
                    ir.vlans[vlan_id].raw_lines.append(line)

            # Firewall (ACLs)
            elif parts[1] == "firewall" and parts[2] == "family" and parts[3] == "inet" and parts[4] == "filter":
                acl_name = parts[5]
                if acl_name not in ir.acls:
                    ir.acls[acl_name] = AclIR(name=acl_name, type="extended", raw_lines=[])
                
                # Simple extraction, deeper translation needed for true perfection
                # We aggregate terms
                if len(parts) > 7 and parts[6] == "term":
                    term = parts[7]
                    # This is rudimentary, but provides the structure
                    ir.acls[acl_name].raw_lines.append(line)
                    
            # Static routes
            elif parts[1] == "routing-options" and parts[2] == "static" and parts[3] == "route":
                prefix = parts[4]
                if len(parts) > 6 and parts[5] == "next-hop":
                    nh = parts[6]
                    ir.static_routes.append(StaticRouteIR(prefix=prefix, next_hop=nh, raw_line=line))

        return ir

    def parse_snippet(self, snippet_text: str) -> DeviceIR:
        return self.parse(snippet_text)
