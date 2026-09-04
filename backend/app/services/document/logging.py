import logging

logger = logging.getLogger("document.ingestion")

def log_parse_event(event: str, **fields):
    logger.info("document_parse %s", event, extra={"document_parse": fields})

def log_evidence_warning(message: str, **fields):
    logger.warning("evidence_resolution %s", message, extra={"evidence": fields})
