# Router Migrate

**Universal Router Configuration Migration Tool**

`router-migrate` is a fully-featured, syntax-aware configuration extraction and migration tool. It allows network engineers to smoothly migrate interfaces, VRFs, VLANs, and routing protocol stanzas from one vendor's configuration format to another, with zero mistakes. 

The tool utilizes an Intermediate Representation (IR) system, allowing it to deeply parse attributes like complex Access Control Lists (ACLs), BGP stanzas, route-maps, and prefix-lists, rather than just doing crude string replacements.

## Features

- **Universal Translation**: Migrate between fundamentally different network operating systems.
- **Deep ACL Translation**: Breaks down permit/deny, protocols, source/destination IPs and masks, and ports to accurately regenerate the ACL for the target vendor.
- **VRF & BGP Awareness**: Accurately extracts route-targets, route-distinguishers, and address-families.
- **Interface Renaming**: Supports passing a mapping to safely rename interfaces during the migration.
- **6 Supported Vendors**: 
  - Arista (EOS)
  - Cisco (IOS/IOS-XE/IOS-XR)
  - Juniper (Junos - Set format)
  - Brocade (FastIron/NetIron)
  - Huawei (VRP)
  - Brocade MLX

## Usage

```bash
python3 -m router_migrate.cli -t <target_interfaces> -s <source_running_config> \
    --source-vendor <vendor> \
    --target-vendor <vendor> \
    [-o output_file] \
    [--new-interface OLD=NEW]
```

### Arguments

- `-t, --target`: A file containing the interface names or a snippet you want to migrate.
- `-s, --source`: The full running-config of the existing router.
- `--source-vendor`: The vendor format of the source config (`arista`, `cisco`, `juniper`, `brocade`, `huawei`, `mlx`).
- `--target-vendor`: The vendor format you wish to generate (`arista`, `cisco`, `juniper`, `brocade`, `huawei`, `mlx`).
- `-o, --output`: Optional output file for the generated config (defaults to stdout).
- `--new-interface`: Rename an interface during generation. (e.g. `--new-interface "ethernet 1/1=Ethernet5"`)

## Architecture

1. **Parsers (`router_migrate/parsers/`)**: Read raw vendor configuration text and compile it into a unified `DeviceIR` (Intermediate Representation).
2. **Analyzers (`router_migrate/analyzers/`)**: Determine what parts of the `DeviceIR` are strictly necessary for the target interfaces being migrated (resolving dependencies like ACLs and VRFs) and compiles a `MigrationIR`.
3. **Generators (`router_migrate/generators/`)**: Takes the `MigrationIR` and emits fully compliant configuration syntax for the destination vendor.

## Requirements

- Python 3.8+
