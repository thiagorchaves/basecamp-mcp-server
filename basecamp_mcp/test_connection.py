from __future__ import annotations

from .client import BasecampClient


def main() -> None:
    client = BasecampClient()
    projects = client.request("GET", "projects.json")
    print("200")
    print(projects)


if __name__ == "__main__":
    main()
