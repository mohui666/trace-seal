"""Bad agent demo: writes a sensitive .env file.

TraceSeal should record a file.write event and mark it with the env_write
policy rule because environment files often contain secrets.
"""

from pathlib import Path


def main() -> None:
    env_path = Path(".env")
    env_path.write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=sk-demo-secret",
                "DATABASE_URL=postgres://demo:demo@localhost/demo",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"bad agent wrote sensitive config to {env_path}")


if __name__ == "__main__":
    main()
