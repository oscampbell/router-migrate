#!/usr/bin/env python3
"""
router-migrate
──────────────
Extracts everything needed to migrate an interface from one router
to another: VRFs, VLANs, ACLs, prefix-lists, route-maps, static routes,
and BGP VRF stanzas — all pulled from the source router's running-config.

Usage:
    python3 -m router_migrate.cli -t <target> -s <source> --source-vendor <sv> --target-vendor <tv> [options]
"""

import argparse
import sys
import os
import logging
import questionary
from router_migrate import __version__
from router_migrate.analyzers.fidelity import check_fidelity
from router_migrate.parsers.mlx import MlxParser
from router_migrate.parsers.arista import AristaParser
from router_migrate.parsers.cisco import CiscoParser
from router_migrate.parsers.juniper import JuniperParser
from router_migrate.parsers.brocade import BrocadeParser
from router_migrate.parsers.huawei import HuaweiParser
from router_migrate.generators.arista import AristaGenerator
from router_migrate.generators.mlx import MlxGenerator
from router_migrate.generators.cisco import CiscoGenerator
from router_migrate.generators.juniper import JuniperGenerator
from router_migrate.generators.brocade import BrocadeGenerator
from router_migrate.generators.huawei import HuaweiGenerator
from router_migrate.parsers.panos import PanosParser
from router_migrate.generators.panos import PanosGenerator
from router_migrate.analyzers.migrator import Migrator

def main():
    parser = argparse.ArgumentParser(
        description="Universal Router Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-t", "--target",
                        help="Target: the interface stanza(s) you want to migrate (use '-' for stdin)")
    parser.add_argument("-s", "--source",
                        help="Source: full running-config of the existing router (use '-' for stdin)")
    parser.add_argument("--source-vendor", choices=["mlx", "arista", "cisco", "juniper", "brocade", "huawei", "panos"],
                        help="Vendor of the source configuration")
    parser.add_argument("--target-vendor", choices=["arista", "mlx", "cisco", "juniper", "brocade", "huawei", "panos"],
                        help="Target vendor to migrate to")
    parser.add_argument("-o", "--output", default=None,
                        help="Output file (default: stdout)")
    parser.add_argument("--validate", action="store_true",
                        help="Run validation and generate a fidelity report")
    parser.add_argument("--serve", action="store_true",
                        help="Start the FastAPI web-based GUI")
    parser.add_argument("-f", "--force", action="store_true",
                        help="Force overwrite if output file already exists")
    parser.add_argument("--new-interface", action="append", default=[],
                        metavar="OLD=NEW",
                        help="Interface rename on new device, e.g. --new-interface ethernet 1/1=Ethernet5")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose logging")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}",
                        help="Show the version of the tool")

    args = parser.parse_args()

    if args.serve:
        print("Starting FastAPI Web Server on http://localhost:8000...")
        import uvicorn
        uvicorn.run("router_migrate.web.app:app", host="127.0.0.1", port=8000, reload=True)
        sys.exit(0)

    if len(sys.argv) == 1:
        print("Welcome to router-migrate TUI Wizard!")
        args.source = questionary.path("Path to source configuration file:").ask()
        args.target = questionary.path("Path to target interface snippet file:").ask()
        vendors = ["mlx", "arista", "cisco", "juniper", "brocade", "huawei", "panos"]
        args.source_vendor = questionary.select("Select Source Vendor:", choices=vendors).ask()
        args.target_vendor = questionary.select("Select Target Vendor:", choices=vendors).ask()
        args.output = questionary.text("Output file (leave blank for stdout):").ask()
        if not args.output:
            args.output = None
        args.validate = questionary.confirm("Run fidelity validation?").ask()
        
    if not all([args.source, args.target, args.source_vendor, args.target_vendor]):
        sys.exit("[error] Missing required arguments.")

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        if args.target == "-":
            target_text = sys.stdin.read()
        else:
            with open(args.target) as f:
                target_text = f.read()

        if args.source == "-":
            if args.target == "-":
                sys.exit("[error] cannot read both target and source from stdin")
            fullconfig_text = sys.stdin.read()
        else:
            with open(args.source) as f:
                fullconfig_text = f.read()
    except FileNotFoundError as e:
        sys.exit(f"[error] {e}")

    # Build renames map
    renames = {}
    for spec in args.new_interface:
        if "=" not in spec:
            sys.exit(f"[error] --new-interface must be OLD=NEW, got: {spec}")
        old, new = spec.split("=", 1)
        renames[old.strip()] = new.strip()

    # 1. Parse
    if args.source_vendor == "mlx":
        parser_obj = MlxParser()
    elif args.source_vendor == "arista":
        parser_obj = AristaParser()
    elif args.source_vendor == "cisco":
        parser_obj = CiscoParser()
    elif args.source_vendor == "juniper":
        parser_obj = JuniperParser()
    elif args.source_vendor == "brocade":
        parser_obj = BrocadeParser()
    elif args.source_vendor == "huawei":
        parser_obj = HuaweiParser()
    elif args.source_vendor == "panos":
        parser_obj = PanosParser()
    else:
        sys.exit(f"[error] unknown source vendor: {args.source_vendor}")

    source_device = parser_obj.parse(fullconfig_text)
    target_snippet = parser_obj.parse_snippet(target_text)

    # 2. Analyze & Extract
    migrator = Migrator(source_device, target_snippet, args.source_vendor, args.target_vendor, renames)
    migration_ir = migrator.analyze()

    # 3. Generate
    if args.target_vendor == "arista":
        generator = AristaGenerator()
    elif args.target_vendor == "mlx":
        generator = MlxGenerator()
    elif args.target_vendor == "cisco":
        generator = CiscoGenerator()
    elif args.target_vendor == "juniper":
        generator = JuniperGenerator()
    elif args.target_vendor == "brocade":
        generator = BrocadeGenerator()
    elif args.target_vendor == "huawei":
        generator = HuaweiGenerator()
    elif args.target_vendor == "panos":
        generator = PanosGenerator()
    else:
        sys.exit(f"[error] unknown target vendor: {args.target_vendor}")

    output_text = generator.generate(migration_ir)

    # Output
    if args.output:
        if os.path.exists(args.output) and not args.force:
            sys.exit(f"[error] Output file '{args.output}' already exists. Use -f or --force to overwrite.")
        with open(args.output, "w") as f:
            f.write(output_text)
        print(f"Output written to: {args.output}")
    else:
        print(output_text)

    # Validation
    if args.validate:
        logging.info("Running fidelity validation...")
        target_parser_class = {
            "mlx": MlxParser,
            "arista": AristaParser,
            "cisco": CiscoParser,
            "juniper": JuniperParser,
            "brocade": BrocadeParser,
            "huawei": HuaweiParser,
            "panos": PanosParser
        }[args.target_vendor]
        target_parser = target_parser_class()
        target_ir = target_parser.parse(output_text)
        warnings = check_fidelity(source_device, target_ir)
        if warnings:
            print("\n--- Fidelity Warnings ---")
            for w in warnings:
                print(w)
            print("-------------------------\n")
        else:
            print("\n--- Validation Successful: No feature drops detected ---\n")

if __name__ == "__main__":
    main()
