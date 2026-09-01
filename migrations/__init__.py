from importlib import import_module
from pathlib import Path


def run_all(engine):
    migration_files = sorted(Path(__file__).parent.glob("*.py"))
    for f in migration_files:
        if f.name.startswith("_"):
            continue
        mod = import_module(f"migrations.{f.stem}")
        mod.migrate(engine)
