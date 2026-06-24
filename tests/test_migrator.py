import pytest
from router_migrate.models import DeviceIR, InterfaceIR, VrfIR, VlanIR, IPAddress
from router_migrate.analyzers.migrator import Migrator

def test_migrator_analyze():
    source = DeviceIR()
    source.vrfs["RED"] = VrfIR(name="RED", raw_lines=[])
    source.vlans["10"] = VlanIR(vlan_id="10", raw_lines=[])
    source.interfaces["GigabitEthernet0/0"] = InterfaceIR(
        name="GigabitEthernet0/0",
        vrf="RED",
        vlan="10",
        ip_addresses=[IPAddress("192.168.1.1", "255.255.255.0")],
        raw_lines=[]
    )
    
    target = DeviceIR()
    target.interfaces["GigabitEthernet0/0"] = InterfaceIR(
        name="GigabitEthernet0/0", raw_lines=[]
    )
    
    renames = {"GigabitEthernet0/0": "Ethernet5"}
    
    migrator = Migrator(
        source_device=source,
        target_snippet=target,
        source_vendor="cisco",
        target_vendor="arista",
        renames=renames
    )
    
    mig_ir = migrator.analyze()
    
    assert mig_ir.source_vendor == "cisco"
    assert mig_ir.target_vendor == "arista"
    
    assert len(mig_ir.interfaces) == 1
    assert mig_ir.interfaces[0].name == "Ethernet5"
    assert mig_ir.interfaces[0].vrf == "RED"
    assert mig_ir.interfaces[0].vlan == "10"
    
    assert len(mig_ir.vrfs) == 1
    assert mig_ir.vrfs[0].name == "RED"
    
    assert len(mig_ir.vlans) == 1
    assert mig_ir.vlans[0].vlan_id == "10"
