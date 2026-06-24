from router_migrate.models import DeviceIR, MigrationIR
from typing import List

def check_fidelity(source_ir: DeviceIR, generated_ir: DeviceIR) -> List[str]:
    """
    Validates that the features present in the source IR exist in the generated IR.
    """
    warnings = []
    
    # Check interfaces
    for if_name, s_iface in source_ir.interfaces.items():
        found = False
        for g_iface in generated_ir.interfaces.values():
            if g_iface.name == s_iface.name or s_iface.name in g_iface.name:
                found = True
                if s_iface.ip_addresses and not g_iface.ip_addresses:
                    warnings.append(f"Warning: Interface {if_name} lost its IP addresses during migration.")
                break
        if not found:
            warnings.append(f"Warning: Interface {if_name} was dropped during migration.")
            
    # Check ACLs
    for acl_name, s_acl in source_ir.acls.items():
        if acl_name not in generated_ir.acls:
            warnings.append(f"Warning: ACL {acl_name} was not generated in the target config.")
            
    # Check BGP
    for vrf_name, s_bgp in source_ir.bgp_vrfs.items():
        if vrf_name not in generated_ir.bgp_vrfs:
            warnings.append(f"Warning: BGP VRF {vrf_name} was dropped during migration.")
            
    return warnings
