import pytest
from router_migrate.models import MigrationIR, VlanIR, InterfaceIR, IPAddress
from router_migrate.generators.arista import AristaGenerator

def test_arista_generator():
    mig_ir = MigrationIR(source_vendor="cisco", target_vendor="arista")
    mig_ir.vlans.append(VlanIR(vlan_id="10", name="DataVlan", raw_lines=[]))
    mig_ir.interfaces.append(InterfaceIR(
        name="Ethernet1", 
        description="Test Port",
        vlan="10",
        enabled=True,
        ip_addresses=[IPAddress("10.0.0.1", "24")],
        raw_lines=[]
    ))
    generator = AristaGenerator()
    out = generator.generate(mig_ir)
    assert "vlan 10" in out
    assert "name DataVlan" in out
    assert "interface Ethernet1" in out
    assert "description Test Port" in out
    assert "encapsulation dot1q vlan 10" in out
    assert "ip address 10.0.0.1/24" in out
    assert "no shutdown" in out
