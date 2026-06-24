import pytest
from router_migrate.models import DeviceIR, InterfaceIR, VrfIR, VlanIR, AclIR, AclRuleIR, IPAddress
from router_migrate.parsers.cisco import CiscoParser
from router_migrate.parsers.arista import AristaParser

def test_cisco_parser_interface():
    config = """
interface GigabitEthernet0/0
 description Test Interface
 vrf forwarding RED
 ip address 192.168.1.1 255.255.255.0
 ip access-group ACL_IN in
 no shutdown
!
"""
    parser = CiscoParser()
    device = parser.parse(config)
    assert "GigabitEthernet0/0" in device.interfaces
    intf = device.interfaces["GigabitEthernet0/0"]
    assert intf.description == "Test Interface"
    assert intf.vrf == "RED"
    assert len(intf.ip_addresses) == 1
    assert intf.ip_addresses[0].address == "192.168.1.1"
    assert intf.ip_addresses[0].mask == "255.255.255.0"
    assert intf.acl_in == "ACL_IN"
    assert intf.enabled is True

def test_arista_parser_vlan():
    config = """
vlan 10
   name DataVlan
!
"""
    parser = AristaParser()
    device = parser.parse(config)
    assert "10" in device.vlans
    assert device.vlans["10"].name == "DataVlan"
