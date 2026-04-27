import re


def parse_js_file(code: str, filepath: str) -> dict:
    """Extract exports, routes, dependencies, and tables from JS/TS code."""
    exports = []
    routes = []
    dependencies = []
    tables = []

    for line in code.split("\n"):
        line_stripped = line.strip()

        # Exports: export function/const/class
        m = re.match(r'export\s+(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', line_stripped)
        if m:
            exports.append(f"{m.group(1)}({m.group(2).strip()})")
            continue

        m = re.match(r'export\s+const\s+(\w+)\s*=', line_stripped)
        if m:
            exports.append(m.group(1))
            continue

        m = re.match(r'export\s+class\s+(\w+)', line_stripped)
        if m:
            exports.append(m.group(1))
            continue

        m = re.match(r'export\s+default\s+(?:class|function)\s+(\w+)', line_stripped)
        if m:
            exports.append(f"{m.group(1)} (default)")
            continue

        # Routes: app.get/post/... or router.get/post/...
        m = re.match(r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]', line_stripped)
        if m:
            method = m.group(1).upper()
            path = m.group(2)
            routes.append(f"{method} {path}")
            continue

        # Dependencies: import ... from '...'
        m = re.match(r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]', line_stripped)
        if m:
            dependencies.append(m.group(1))
            continue

        # Tables: pgTable, createTable, etc.
        m = re.match(r'export\s+const\s+(\w+)\s*=\s*(?:pgTable|mysqlTable|sqliteTable|createTable)\s*\(\s*[\'"](\w+)[\'"]', line_stripped)
        if m:
            table_name = m.group(2)
            tables.append(f"table {table_name}")

    # Multi-line table detection: look for pgTable patterns
    for m in re.finditer(r'(?:pgTable|mysqlTable|sqliteTable)\s*\(\s*[\'"](\w+)[\'"]', code):
        table_name = m.group(1)
        entry = f"table {table_name}"
        if entry not in tables:
            tables.append(entry)

    return {"exports": exports, "routes": routes, "dependencies": dependencies, "tables": tables}


def parse_python_file(code: str, filepath: str) -> dict:
    """Extract functions, classes, routes, dependencies, and tables from Python code."""
    exports = []
    routes = []
    dependencies = []
    tables = []

    lines = code.split("\n")
    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Top-level functions (not indented)
        if line_stripped.startswith("def ") and not line.startswith(" ") and not line.startswith("\t"):
            m = re.match(r'def\s+(\w+)\s*\(([^)]*)\)', line_stripped)
            if m:
                exports.append(f"{m.group(1)}({m.group(2).strip()})")

        # Top-level async functions
        if line_stripped.startswith("async def ") and not line.startswith(" ") and not line.startswith("\t"):
            m = re.match(r'async\s+def\s+(\w+)\s*\(([^)]*)\)', line_stripped)
            if m:
                exports.append(f"{m.group(1)}({m.group(2).strip()})")

        # Classes
        if line_stripped.startswith("class ") and not line.startswith(" ") and not line.startswith("\t"):
            m = re.match(r'class\s+(\w+)', line_stripped)
            if m:
                exports.append(m.group(1))

        # Routes: @app.get/post/... or @router.get/post/...
        m = re.match(r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]', line_stripped)
        if m:
            method = m.group(1).upper()
            path = m.group(2)
            routes.append(f"{method} {path}")

        # Flask routes: @app.route
        m = re.match(r'@(?:app|blueprint|bp)\.route\s*\(\s*[\'"]([^\'"]+)[\'"]', line_stripped)
        if m:
            routes.append(f"ROUTE {m.group(1)}")

        # Dependencies: from X import / import X
        m = re.match(r'from\s+([\w.]+)\s+import', line_stripped)
        if m:
            dependencies.append(m.group(1))
            continue
        m = re.match(r'import\s+([\w.]+)', line_stripped)
        if m:
            dependencies.append(m.group(1))

        # Tables: __tablename__
        m = re.match(r"__tablename__\s*=\s*['\"](\w+)['\"]", line_stripped)
        if m:
            tables.append(f"table {m.group(1)}")

    return {"exports": exports, "routes": routes, "dependencies": dependencies, "tables": tables}


def generate_file_description(parsed: dict) -> str:
    """Generate a one-line description from parsed file data."""
    parts = []
    if parsed["routes"]:
        parts.append(f"{len(parsed['routes'])} route(s): {', '.join(parsed['routes'][:3])}")
    if parsed["tables"]:
        parts.append(f"tables: {', '.join(parsed['tables'])}")
    if parsed["exports"] and not parsed["routes"]:
        names = [e.split("(")[0] for e in parsed["exports"][:4]]
        parts.append(f"{len(parsed['exports'])} exports: {', '.join(names)}")
    if not parts:
        return "no public exports detected"
    return "; ".join(parts)
