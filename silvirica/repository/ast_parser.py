from __future__ import annotations
import ast
import re
from pathlib import Path
from typing import List, Optional
from silvirica.core.types import SymbolInfo, SymbolKind


class MultiLanguageASTParser:
    """
    Structural code intelligence parser supporting Python AST and multi-language
    structural heuristic extractors (JS/TS, PHP, Java, Go, Rust, SQL, C#).
    """

    @classmethod
    def parse_file(cls, file_path: Path, root_path: Optional[Path] = None) -> List[SymbolInfo]:
        if not file_path.exists() or not file_path.is_file():
            return []

        rel_path = str(file_path.relative_to(root_path)).replace("\\", "/") if root_path else str(file_path)
        ext = file_path.suffix.lower()

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        if ext == ".py":
            return cls._parse_python(content, rel_path)
        elif ext in [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]:
            return cls._parse_javascript_typescript(content, rel_path)
        elif ext in [".php", ".phtml"]:
            return cls._parse_php(content, rel_path)
        elif ext in [".go"]:
            return cls._parse_go(content, rel_path)
        elif ext in [".rs"]:
            return cls._parse_rust(content, rel_path)
        elif ext in [".java", ".kt", ".cs"]:
            return cls._parse_c_family(content, rel_path)
        elif ext in [".sql"]:
            return cls._parse_sql(content, rel_path)
        else:
            return cls._parse_generic(content, rel_path)

    @classmethod
    def _parse_python(cls, content: str, rel_path: str) -> List[SymbolInfo]:
        symbols: List[SymbolInfo] = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return cls._parse_generic(content, rel_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or ""
                symbols.append(
                    SymbolInfo(
                        name=node.name,
                        kind=SymbolKind.CLASS,
                        file_path=rel_path,
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        docstring=doc,
                    )
                )
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        params = [arg.arg for arg in child.args.args]
                        m_doc = ast.get_docstring(child) or ""
                        sig = f"{child.name}({', '.join(params)})"
                        symbols.append(
                            SymbolInfo(
                                name=child.name,
                                kind=SymbolKind.METHOD,
                                file_path=rel_path,
                                start_line=child.lineno,
                                end_line=getattr(child, "end_lineno", child.lineno),
                                container=node.name,
                                signature=sig,
                                docstring=m_doc,
                                parameters=params,
                            )
                        )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Only top-level functions (not inside ClassDef)
                if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) if hasattr(parent, 'body') and node in getattr(parent, 'body', [])):
                    params = [arg.arg for arg in child.args.args] if hasattr(node, "child") else [arg.arg for arg in node.args.args]
                    doc = ast.get_docstring(node) or ""
                    sig = f"{node.name}({', '.join(params)})"
                    symbols.append(
                        SymbolInfo(
                            name=node.name,
                            kind=SymbolKind.FUNCTION,
                            file_path=rel_path,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            signature=sig,
                            docstring=doc,
                            parameters=params,
                        )
                    )

        return symbols

    @classmethod
    def _parse_javascript_typescript(cls, content: str, rel_path: str) -> List[SymbolInfo]:
        symbols: List[SymbolInfo] = []
        lines = content.splitlines()

        class_pat = re.compile(r'^\s*(?:export\s+)?(?:default\s+)?class\s+([A-Za-z0-9_$]+)')
        func_pat = re.compile(r'^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(([^)]*)\)')
        arrow_pat = re.compile(r'^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>')
        interface_pat = re.compile(r'^\s*(?:export\s+)?interface\s+([A-Za-z0-9_$]+)')
        route_pat = re.compile(r'(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]')

        for idx, line in enumerate(lines, 1):
            c_match = class_pat.search(line)
            if c_match:
                symbols.append(
                    SymbolInfo(
                        name=c_match.group(1),
                        kind=SymbolKind.CLASS,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                    )
                )
                continue

            f_match = func_pat.search(line)
            if f_match:
                name = f_match.group(1)
                params = [p.strip().split(":")[0].strip() for p in f_match.group(2).split(",") if p.strip()]
                symbols.append(
                    SymbolInfo(
                        name=name,
                        kind=SymbolKind.FUNCTION,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                        signature=f"{name}({', '.join(params)})",
                        parameters=params,
                    )
                )
                continue

            a_match = arrow_pat.search(line)
            if a_match:
                name = a_match.group(1)
                params = [p.strip().split(":")[0].strip() for p in a_match.group(2).split(",") if p.strip()]
                is_component = name[0].isupper() and (rel_path.endswith(".tsx") or rel_path.endswith(".jsx"))
                symbols.append(
                    SymbolInfo(
                        name=name,
                        kind=SymbolKind.COMPONENT if is_component else SymbolKind.FUNCTION,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                        signature=f"{name}({', '.join(params)})",
                        parameters=params,
                    )
                )
                continue

            i_match = interface_pat.search(line)
            if i_match:
                symbols.append(
                    SymbolInfo(
                        name=i_match.group(1),
                        kind=SymbolKind.INTERFACE,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                    )
                )
                continue

            r_match = route_pat.search(line)
            if r_match:
                verb = r_match.group(1).upper()
                route_path = r_match.group(2)
                symbols.append(
                    SymbolInfo(
                        name=f"{verb} {route_path}",
                        kind=SymbolKind.ROUTE,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                        signature=f"{verb} {route_path}",
                    )
                )

        return symbols

    @classmethod
    def _parse_php(cls, content: str, rel_path: str) -> List[SymbolInfo]:
        symbols: List[SymbolInfo] = []
        lines = content.splitlines()

        class_pat = re.compile(r'^\s*(?:final\s+|abstract\s+)?class\s+([A-Za-z0-9_]+)')
        func_pat = re.compile(r'^\s*(?:public|protected|private|static|\s)*function\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)')
        laravel_route_pat = re.compile(r'Route::(get|post|put|delete|patch|match|any)\s*\(\s*[\'"]([^\'"]+)[\'"]')

        current_class: Optional[str] = None

        for idx, line in enumerate(lines, 1):
            c_match = class_pat.search(line)
            if c_match:
                current_class = c_match.group(1)
                symbols.append(
                    SymbolInfo(
                        name=current_class,
                        kind=SymbolKind.CLASS,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                    )
                )
                continue

            f_match = func_pat.search(line)
            if f_match:
                name = f_match.group(1)
                params = [p.strip() for p in f_match.group(2).split(",") if p.strip()]
                symbols.append(
                    SymbolInfo(
                        name=name,
                        kind=SymbolKind.METHOD if current_class else SymbolKind.FUNCTION,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                        container=current_class,
                        signature=f"{name}({', '.join(params)})",
                        parameters=params,
                    )
                )
                continue

            r_match = laravel_route_pat.search(line)
            if r_match:
                verb = r_match.group(1).upper()
                r_path = r_match.group(2)
                symbols.append(
                    SymbolInfo(
                        name=f"{verb} {r_path}",
                        kind=SymbolKind.ROUTE,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                        signature=f"Route::{verb.lower()}('{r_path}')",
                    )
                )

        return symbols

    @classmethod
    def _parse_go(cls, content: str, rel_path: str) -> List[SymbolInfo]:
        symbols: List[SymbolInfo] = []
        lines = content.splitlines()
        func_pat = re.compile(r'^func\s+(?:\(([^)]+)\)\s+)?([A-Za-z0-9_]+)\s*\(([^)]*)\)')
        type_pat = re.compile(r'^type\s+([A-Za-z0-9_]+)\s+(struct|interface)')

        for idx, line in enumerate(lines, 1):
            t_match = type_pat.search(line)
            if t_match:
                symbols.append(
                    SymbolInfo(
                        name=t_match.group(1),
                        kind=SymbolKind.CLASS if t_match.group(2) == "struct" else SymbolKind.INTERFACE,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                    )
                )
                continue

            f_match = func_pat.search(line)
            if f_match:
                receiver = f_match.group(1)
                name = f_match.group(2)
                symbols.append(
                    SymbolInfo(
                        name=name,
                        kind=SymbolKind.METHOD if receiver else SymbolKind.FUNCTION,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                        container=receiver.strip() if receiver else None,
                    )
                )

        return symbols

    @classmethod
    def _parse_rust(cls, content: str, rel_path: str) -> List[SymbolInfo]:
        symbols: List[SymbolInfo] = []
        lines = content.splitlines()
        fn_pat = re.compile(r'^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)')
        struct_pat = re.compile(r'^\s*(?:pub\s+)?(struct|enum|trait)\s+([A-Za-z0-9_]+)')

        for idx, line in enumerate(lines, 1):
            s_match = struct_pat.search(line)
            if s_match:
                symbols.append(
                    SymbolInfo(
                        name=s_match.group(2),
                        kind=SymbolKind.CLASS,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                    )
                )
                continue

            f_match = fn_pat.search(line)
            if f_match:
                name = f_match.group(1)
                symbols.append(
                    SymbolInfo(
                        name=name,
                        kind=SymbolKind.FUNCTION,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                    )
                )

        return symbols

    @classmethod
    def _parse_c_family(cls, content: str, rel_path: str) -> List[SymbolInfo]:
        symbols: List[SymbolInfo] = []
        lines = content.splitlines()
        class_pat = re.compile(r'^\s*(?:public|private|protected|internal)?\s*(?:class|interface|record)\s+([A-Za-z0-9_]+)')
        method_pat = re.compile(r'^\s*(?:public|private|protected|static|\s)+[A-Za-z0-9_<>[\]]+\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*[{;]')

        for idx, line in enumerate(lines, 1):
            c_match = class_pat.search(line)
            if c_match:
                symbols.append(
                    SymbolInfo(
                        name=c_match.group(1),
                        kind=SymbolKind.CLASS,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                    )
                )
                continue

            m_match = method_pat.search(line)
            if m_match:
                symbols.append(
                    SymbolInfo(
                        name=m_match.group(1),
                        kind=SymbolKind.METHOD,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                    )
                )

        return symbols

    @classmethod
    def _parse_sql(cls, content: str, rel_path: str) -> List[SymbolInfo]:
        symbols: List[SymbolInfo] = []
        lines = content.splitlines()
        table_pat = re.compile(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[`"\[]?)([A-Za-z0-9_]+)', re.IGNORECASE)
        for idx, line in enumerate(lines, 1):
            m = table_pat.search(line)
            if m:
                symbols.append(
                    SymbolInfo(
                        name=m.group(1),
                        kind=SymbolKind.DATABASE_TABLE,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                    )
                )
        return symbols

    @classmethod
    def _parse_generic(cls, content: str, rel_path: str) -> List[SymbolInfo]:
        return []
