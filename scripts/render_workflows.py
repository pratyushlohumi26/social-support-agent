"""Render all LangGraph-based workflows in the repository as PNG diagrams."""

import importlib
import inspect
import pkgutil
from pathlib import Path

OUTPUT_DIR = Path("workflow_diagrams")
OUTPUT_DIR.mkdir(exist_ok=True)


def find_workflows(package_name: str):
    """Recursively find classes ending with 'Workflow' inside a package."""
    try:
        pkg = importlib.import_module(package_name)
    except ModuleNotFoundError:
        return []

    results = []
    for _, modname, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        if ispkg:
            continue
        module = importlib.import_module(modname)
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name.endswith("Workflow"):
                results.append(obj)
    return results


def render_workflow(workflow_cls):
    name = workflow_cls.__name__
    print(f"Rendering {name} ...")

    try:
        wf_instance = workflow_cls()
        graph = getattr(wf_instance, "workflow", None)
        if graph is None and hasattr(wf_instance, "get_graph"):
            graph = wf_instance.get_graph()

        if not graph:
            print(f"[WARN] {name} has no graph instance.")
            return

        if hasattr(graph, "draw_mermaid_png"):
            png_data = graph.draw_mermaid_png()
            out_path = OUTPUT_DIR / f"{name}.png"
            with open(out_path, "wb") as f:
                f.write(png_data)
            print(f"✅ {name} diagram saved to {out_path}")
        elif hasattr(graph, "draw_mermaid"):
            code = graph.draw_mermaid()
            out_path = OUTPUT_DIR / f"{name}.mmd"
            with open(out_path, "w") as f:
                f.write(code)
            print(f"⚠️ {name} Mermaid file saved (no PNG backend); use mmdc to render.")
        else:
            print(f"[WARN] Graph for {name} cannot be visualized (no draw_* method).")
    except Exception as e:
        print(f"❌ Failed to render {name}: {e}")


def main():
    print("Scanning for workflow classes...")
    workflow_classes = find_workflows("src.orchestration")

    if not workflow_classes:
        print("No workflows found.")
        return

    for cls in workflow_classes:
        render_workflow(cls)


if __name__ == "__main__":
    main()
