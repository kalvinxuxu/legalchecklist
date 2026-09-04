"""Optional MinerU boundary for complex layouts."""
class MinerUAdapter:
    name = "mineru"
    version = "optional"
    def parse(self, file_path: str, document_id: str, version_id: str):
        raise RuntimeError("MinerU adapter requires the configured Railway worker")
