"""The ``inbox_import`` job's step."""

from operonx import op

from inbox import importer


@op
def import_inbox(tick: int = None, at: str = None) -> dict:
    """Every READY package through the checks (every 10 minutes, BRD-RULE-AI-13)."""
    return {"imported": importer.run_ready()}
