from typing import List, Dict


class SystemTools:
    # These must pass through a security/policy layer before execution
    def run_powershell(self, command: str) -> str:
        return "Success"

    def read_file(self, path: str) -> str:
        return ""

    def write_file(self, path: str, content: str) -> bool:
        return True

    def list_processes(self) -> List[Dict]:
        return []
