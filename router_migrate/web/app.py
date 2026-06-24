import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from router_migrate.parsers.mlx import MlxParser
from router_migrate.parsers.arista import AristaParser
from router_migrate.parsers.cisco import CiscoParser
from router_migrate.parsers.juniper import JuniperParser
from router_migrate.parsers.brocade import BrocadeParser
from router_migrate.parsers.huawei import HuaweiParser
from router_migrate.parsers.panos import PanosParser

from router_migrate.generators.arista import AristaGenerator
from router_migrate.generators.mlx import MlxGenerator
from router_migrate.generators.cisco import CiscoGenerator
from router_migrate.generators.juniper import JuniperGenerator
from router_migrate.generators.brocade import BrocadeGenerator
from router_migrate.generators.huawei import HuaweiGenerator
from router_migrate.generators.panos import PanosGenerator

from router_migrate.analyzers.migrator import Migrator

app = FastAPI(title="Router Migrate Web UI")

class MigrationRequest(BaseModel):
    source_config: str
    target_config: str
    source_vendor: str
    target_vendor: str

class MigrationResponse(BaseModel):
    output: str

PARSERS = {
    "mlx": MlxParser,
    "arista": AristaParser,
    "cisco": CiscoParser,
    "juniper": JuniperParser,
    "brocade": BrocadeParser,
    "huawei": HuaweiParser,
    "panos": PanosParser,
}

GENERATORS = {
    "arista": AristaGenerator,
    "mlx": MlxGenerator,
    "cisco": CiscoGenerator,
    "juniper": JuniperGenerator,
    "brocade": BrocadeGenerator,
    "huawei": HuaweiGenerator,
    "panos": PanosGenerator,
}

@app.post("/api/migrate", response_model=MigrationResponse)
def api_migrate(req: MigrationRequest):
    if req.source_vendor not in PARSERS:
        raise HTTPException(status_code=400, detail=f"Unknown source vendor: {req.source_vendor}")
    if req.target_vendor not in GENERATORS:
        raise HTTPException(status_code=400, detail=f"Unknown target vendor: {req.target_vendor}")

    try:
        parser_obj = PARSERS[req.source_vendor]()
        source_device = parser_obj.parse(req.source_config)
        target_snippet = parser_obj.parse_snippet(req.target_config)

        # Migrator takes renames as the 5th argument, we pass an empty dict
        migrator = Migrator(source_device, target_snippet, req.source_vendor, req.target_vendor, {})
        migration_ir = migrator.analyze()

        generator = GENERATORS[req.target_vendor]()
        output_text = generator.generate(migration_ir)

        return MigrationResponse(output=output_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Web UI is not initialized. index.html not found in static directory."}
