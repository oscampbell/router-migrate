import os
import subprocess
import itertools

VENDORS = ["mlx", "arista", "cisco", "juniper", "brocade", "huawei"]

CONFIGS = {
    "mlx": """
vrf RED
 rd 1:1
 route-target both 1:1
!
vlan 10
 name Servers
!
ip access-list extended SERVER-IN
 permit tcp any host 10.0.0.1 eq 80 log
 permit ip any any
!
interface ethernet 1/1
 port-name UPLINK
 vrf forwarding RED
 ip address 10.0.0.1/24
 ip access-group SERVER-IN in
 enable
!
router bgp
 address-family ipv4 unicast vrf RED
  neighbor 10.0.0.2 remote-as 65001
!
ip route vrf RED 0.0.0.0/0 10.0.0.254
""",
    "brocade": """
vrf RED
 rd 1:1
 route-target both 1:1
!
vlan 10
 name Servers
!
ip access-list extended SERVER-IN
 permit tcp any host 10.0.0.1 eq 80 log
 permit ip any any
!
interface ethernet 1/1
 port-name UPLINK
 vrf forwarding RED
 ip address 10.0.0.1/24
 ip access-group SERVER-IN in
 enable
!
router bgp
 address-family ipv4 unicast vrf RED
  neighbor 10.0.0.2 remote-as 65001
!
ip route vrf RED 0.0.0.0/0 10.0.0.254
""",
    "arista": """
vrf instance RED
 rd 1:1
 route-target both 1:1
!
vlan 10
 name Servers
!
ip access-list extended SERVER-IN
 permit tcp any host 10.0.0.1 eq 80 log
 permit ip any any
!
interface Ethernet1
 description UPLINK
 vrf RED
 ip address 10.0.0.1/24
 ip access-group SERVER-IN in
 no shutdown
!
router bgp 65000
 vrf RED
  neighbor 10.0.0.2 remote-as 65001
!
ip route vrf RED 0.0.0.0/0 10.0.0.254
""",
    "cisco": """
vrf definition RED
 rd 1:1
 route-target both 1:1
!
vlan 10
 name Servers
!
ip access-list extended SERVER-IN
 permit tcp any host 10.0.0.1 eq 80 log
 permit ip any any
!
interface GigabitEthernet0/0
 description UPLINK
 vrf forwarding RED
 ip address 10.0.0.1 255.255.255.0
 ip access-group SERVER-IN in
 no shutdown
!
router bgp 65000
 address-family ipv4 vrf RED
  neighbor 10.0.0.2 remote-as 65001
!
ip route vrf RED 0.0.0.0 0.0.0.0 10.0.0.254
""",
    "juniper": """
set vlans Servers vlan-id 10
set routing-instances RED instance-type vrf
set routing-instances RED route-distinguisher 1:1
set routing-instances RED vrf-target target:1:1
set routing-instances RED interface ge-0/0/0.0
set interfaces ge-0/0/0 description "UPLINK"
set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24
set interfaces ge-0/0/0 unit 0 family inet filter input SERVER-IN
set firewall family inet filter SERVER-IN term 10 from protocol tcp
set firewall family inet filter SERVER-IN term 10 from destination-address 10.0.0.1/32
set firewall family inet filter SERVER-IN term 10 from destination-port 80
set firewall family inet filter SERVER-IN term 10 then accept
set firewall family inet filter SERVER-IN term 10 then log
set firewall family inet filter SERVER-IN term 20 from protocol ip
set firewall family inet filter SERVER-IN term 20 then accept
set routing-options static route 0.0.0.0/0 next-hop 10.0.0.254
""",
    "huawei": """
vlan 10
 name Servers
#
ip vpn-instance RED
 ipv4-family
  route-distinguisher 1:1
  vpn-target 1:1 both
#
acl name SERVER-IN advance
 rule 5 permit tcp destination 10.0.0.1 0 destination-port eq 80 logging
 rule 10 permit ip
#
interface GigabitEthernet0/0/1
 description UPLINK
 ip binding vpn-instance RED
 ip address 10.0.0.1 24
 traffic-filter inbound acl SERVER-IN
 undo shutdown
#
bgp 65000
 ipv4-family vpn-instance RED
  peer 10.0.0.2 as-number 65001
#
ip route-static vpn-instance RED 0.0.0.0 0 10.0.0.254
"""
}

TARGETS = {
    "mlx": "interface ethernet 1/1\n vrf forwarding RED\n ip address 10.0.0.1/24\n ip access-group SERVER-IN in\n enable\n",
    "brocade": "interface ethernet 1/1\n vrf forwarding RED\n ip address 10.0.0.1/24\n ip access-group SERVER-IN in\n enable\n",
    "arista": "interface Ethernet1\n vrf RED\n ip address 10.0.0.1/24\n ip access-group SERVER-IN in\n no shutdown\n",
    "cisco": "interface GigabitEthernet0/0\n vrf forwarding RED\n ip address 10.0.0.1 255.255.255.0\n ip access-group SERVER-IN in\n no shutdown\n",
    "juniper": "set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24\nset interfaces ge-0/0/0 unit 0 family inet filter input SERVER-IN\n",
    "huawei": "interface GigabitEthernet0/0/1\n ip binding vpn-instance RED\n ip address 10.0.0.1 24\n traffic-filter inbound acl SERVER-IN\n"
}

def main():
    os.makedirs("test_configs", exist_ok=True)
    
    for v in VENDORS:
        with open(f"test_configs/source_{v}.cfg", "w") as f:
            f.write(CONFIGS[v])
        with open(f"test_configs/target_{v}.cfg", "w") as f:
            f.write(TARGETS[v])
            
    successes = 0
    failures = 0
            
    for src, dst in itertools.product(VENDORS, repeat=2):
        print(f"Testing {src} -> {dst}...", end=" ")
        
        cmd = [
            "python3", "-m", "router_migrate.cli",
            "-s", f"test_configs/source_{src}.cfg",
            "-t", f"test_configs/target_{src}.cfg",
            "--source-vendor", src,
            "--target-vendor", dst
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print("OK")
            successes += 1
            with open(f"test_configs/out_{src}_to_{dst}.cfg", "w") as f:
                f.write(res.stdout)
        else:
            print("FAILED")
            print(res.stderr)
            failures += 1
            
    print(f"\nCompleted: {successes} passed, {failures} failed.")
    if failures > 0:
        exit(1)

if __name__ == "__main__":
    main()
