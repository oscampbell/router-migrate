# Router Migrate

**Universal Router Configuration Migration Tool**

`router-migrate` is a fully-featured, syntax-aware configuration extraction and migration tool. It allows network engineers, IT professionals, and system administrators to smoothly translate interfaces, VRFs, VLANs, and routing protocols from one vendor's configuration format to another, without needing to rewrite hundreds of lines of code manually. 

Instead of just doing simple "find and replace" text editing, `router-migrate` actually "reads" and understands your network configuration, extracting the deep meaning behind ACLs, BGP stanzas, and route-maps, and then writes a brand new configuration tailored perfectly for your target device.

---

## 🌟 Supported Vendors

We currently support migrating between 7 major networking platforms:
- **Arista** (EOS)
- **Cisco** (IOS/IOS-XE/IOS-XR)
- **Juniper** (Junos - Set format)
- **Brocade** (FastIron/NetIron)
- **Huawei** (VRP)
- **Brocade MLX**
- **Palo Alto Networks** (PAN-OS Firewalls)

---

## 📖 Detailed User Guide

We've designed `router-migrate` to be incredibly easy to use, whether you prefer a graphical web interface, an interactive terminal wizard, or running automated scripts.

### 1. The Web UI (Easiest Method)
If you aren't comfortable with command-line arguments, you can use our built-in web interface. It provides a beautiful, side-by-side view where you can simply paste your configurations.

To start the Web UI:
```bash
router-migrate --serve
```
*Then, open your web browser and navigate to `http://localhost:8000`.*

**How to use it:**
1. Select your **Source Vendor** (what you are migrating from) and your **Target Vendor** (what you are migrating to) from the dropdown menus.
2. Paste your entire existing router configuration into the "Source" box.
3. Paste the specific interface names or snippets you want to migrate into the "Target" box.
4. Click **Migrate**. The newly translated configuration will appear instantly at the bottom of the page, ready to be copied!

### 2. The Interactive Wizard (TUI)
If you prefer working in the terminal but don't want to type out long commands, simply run the tool with no arguments:
```bash
router-migrate
```
A friendly interactive wizard will appear! It will ask you step-by-step:
- What is the path to your source configuration file?
- What are you migrating to?
- Would you like to run a fidelity check?

Just use your arrow keys to select options and hit Enter!

### 3. The Command Line Interface (For Automation/Power Users)
If you want to run `router-migrate` as part of a script or prefer explicit commands, use the standard CLI format:

```bash
router-migrate -t target_snippet.txt -s full_running_config.txt \
    --source-vendor cisco \
    --target-vendor arista \
    -o new_arista_config.txt
```

**Advanced CLI Features:**
- **Standard Input (Piping)**: You can use `-` instead of a filename to pipe configurations directly into the tool (e.g., `cat config.txt | router-migrate -s - ...`).
- **Validation Check (`--validate`)**: Worried that a complex ACL rule or IP address might get dropped because the new vendor doesn't support it? Add the `--validate` flag! The tool will double-check the generated configuration and warn you if any features were lost in translation.
- **Verbose Logging (`-v`)**: Add `-v` to see detailed, under-the-hood debugging information about how the tool is mapping your configuration.
- **Interface Renaming**: Use `--new-interface "OLD=NEW"` to automatically rename interfaces during translation (e.g., `--new-interface "GigabitEthernet0/0=Ethernet5"`).

---

## 🛠 Installation

`router-migrate` requires **Python 3.8+**. It uses modern Python packaging, making it easy to install.

1. Clone the repository:
   ```bash
   git clone https://github.com/oscampbell/router-migrate.git
   cd router-migrate
   ```
2. Install the tool and its dependencies:
   ```bash
   pip install .
   ```
   *(Note: This will automatically install requirements like `FastAPI` for the Web UI and `Questionary` for the interactive wizard).*

---

## 🏗 Architecture (For Developers)

If you are interested in how the tool works under the hood:
1. **Parsers (`router_migrate/parsers/`)**: Read raw vendor configuration text and compile it into a unified `DeviceIR` (Intermediate Representation).
2. **Analyzers (`router_migrate/analyzers/`)**: Determine what parts of the `DeviceIR` are strictly necessary for the target interfaces being migrated (resolving dependencies like ACLs and VRFs) and compiles a `MigrationIR`. Also contains the `fidelity` module for validation checks.
3. **Generators (`router_migrate/generators/`)**: Takes the `MigrationIR` and emits fully compliant configuration syntax for the destination vendor.
4. **Web UI (`router_migrate/web/`)**: A FastAPI server bridging the Python migration engine with a Vanilla CSS/JS frontend.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.
