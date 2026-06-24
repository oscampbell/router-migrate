import re
from typing import List
from router_migrate.parsers.base import BaseParser
from router_migrate.models import DeviceIR, InterfaceIR, IPAddress

class PanosParser(BaseParser):
    def parse(self, config_text: str) -> DeviceIR:
        device = DeviceIR()
        current_interface = None
        
        for line in config_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            # Basic set-based PAN-OS extraction for interfaces
            if line.startswith("set network interface ethernet"):
                parts = line.split()
                if len(parts) >= 5:
                    if_name = parts[4]
                    if if_name not in device.interfaces:
                        device.interfaces[if_name] = InterfaceIR(name=if_name)
                    current_interface = device.interfaces[if_name]
                    current_interface.raw_lines.append(line)
                    
                    # set network interface ethernet ethernet1/1 layer3 ip 10.0.0.1/24
                    if "ip" in parts:
                        ip_index = parts.index("ip")
                        if ip_index + 1 < len(parts):
                            ip_str = parts[ip_index + 1]
                            if "/" in ip_str:
                                ip, mask = ip_str.split("/", 1)
                                current_interface.ip_addresses.append(IPAddress(address=ip, mask=mask))
            
        return device

    def parse_snippet(self, snippet_text: str) -> DeviceIR:
        return self.parse(snippet_text)
