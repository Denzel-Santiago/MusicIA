from __future__ import annotations

import ast
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def _module_name(path: Path) -> str:
    relative = path.relative_to(APP_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return "app" + ("." + ".".join(parts) if parts else "")


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


class LayerDependencyTests(unittest.TestCase):
    def test_domain_and_application_do_not_import_infrastructure(self) -> None:
        forbidden = (
            "app.adapters",
            "app.database",
            "app.models",
            "app.services",
            "app.routes",
            "fastapi",
            "sqlalchemy",
            "requests",
            "mutagen",
            "numpy",
            "librosa",
        )
        for layer in ("domain", "application"):
            for path in (APP_ROOT / layer).rglob("*.py"):
                for imported in _imports(path):
                    self.assertFalse(
                        imported.startswith(forbidden),
                        f"{path.relative_to(APP_ROOT)} imports {imported}",
                    )

    def test_routes_do_not_import_adapters_or_persistence_models(self) -> None:
        forbidden = ("app.adapters", "app.database", "app.models", "app.services")
        for path in (APP_ROOT / "routes").rglob("*.py"):
            for imported in _imports(path):
                self.assertFalse(
                    imported.startswith(forbidden),
                    f"{path.relative_to(APP_ROOT)} imports {imported}",
                )

    def test_internal_import_graph_has_no_cycles(self) -> None:
        paths = list(APP_ROOT.rglob("*.py"))
        module_paths = {_module_name(path): path for path in paths}
        graph: dict[str, set[str]] = {module: set() for module in module_paths}
        for module, path in module_paths.items():
            for imported in _imports(path):
                if imported in module_paths:
                    graph[module].add(imported)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(module: str, trail: list[str]) -> None:
            if module in visiting:
                cycle = trail[trail.index(module):] + [module]
                self.fail("Import cycle: " + " -> ".join(cycle))
            if module in visited:
                return
            visiting.add(module)
            trail.append(module)
            for dependency in graph[module]:
                visit(dependency, trail)
            trail.pop()
            visiting.remove(module)
            visited.add(module)

        for module in graph:
            visit(module, [])


if __name__ == "__main__":
    unittest.main()
