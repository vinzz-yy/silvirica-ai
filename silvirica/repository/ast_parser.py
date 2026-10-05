from __future__ import annotations
import ast
import re
from pathlib import Path
from typing import List, Optional, Tuple
from silvirica.core.types import AstRelation, RelationKind, SymbolInfo, SymbolKind


class MultiLanguageASTParser:
    """
    Structural code intelligence parser supporting Python AST and multi-language
    structural heuristic extractors (JS/TS, PHP, Java, Go, Rust, SQL, C#).
    Extracts both symbols and relationship edges (IMPORTS, CALLS, ROUTES_TO, USES, DEPENDS_ON).
    """

    @classmethod
    def parse_file(cls, file_path: Path, root_path: Optional[Path] = None) -> List[SymbolInfo]:
        symbols, _ = cls.parse_file_with_relations(file_path, root_path)
        return symbols

    @classmethod
    def parse_file_with_relations(
        cls, file_path: Path, root_path: Optional[Path] = None
    ) -> Tuple[List[SymbolInfo], List[AstRelation]]:
        if not file_path.exists() or not file_path.is_file():
            return [], []

        rel_path = str(file_path.relative_to(root_path)).replace("\\", "/") if root_path else str(file_path)
        ext = file_path.suffix.lower()

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return [], []

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
            return cls._parse_generic(content, rel_path), []

    @classmethod
    def _parse_python(cls, content: str, rel_path: str) -> Tuple[List[SymbolInfo], List[AstRelation]]:
        symbols: List[SymbolInfo] = []
        relations: List[AstRelation] = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return cls._parse_generic(content, rel_path), []

        file_node_id = f"file:{rel_path}"

        # 1. Imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    relations.append(
                        AstRelation(
                            source_identifier=file_node_id,
                            target_name=alias.name,
                            relation=RelationKind.IMPORTS,
                            file_path=rel_path,
                            line_number=node.lineno,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imported_name = f"{module}.{alias.name}" if module else alias.name
                    relations.append(
                        AstRelation(
                            source_identifier=file_node_id,
                            target_name=imported_name,
                            relation=RelationKind.IMPORTS,
                            file_path=rel_path,
                            line_number=node.lineno,
                        )
                    )

        # 2. Classes & Functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or ""
                class_id = f"sym:{rel_path}:{node.name}"
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

                # Base classes (inheritance)
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        relations.append(
                            AstRelation(
                                source_identifier=class_id,
                                target_name=base.id,
                                relation=RelationKind.DEPENDS_ON,
                                file_path=rel_path,
                                line_number=node.lineno,
                                properties={"type": "extends"},
                            )
                        )
                    elif isinstance(base, ast.Attribute):
                        relations.append(
                            AstRelation(
                                source_identifier=class_id,
                                target_name=base.attr,
                                relation=RelationKind.DEPENDS_ON,
                                file_path=rel_path,
                                line_number=node.lineno,
                                properties={"type": "extends"},
                            )
                        )

                # Methods inside class
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        params = [arg.arg for arg in child.args.args]
                        m_doc = ast.get_docstring(child) or ""
                        sig = f"{child.name}({', '.join(params)})"
                        method_id = f"sym:{rel_path}:{node.name}::{child.name}"
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
                        # Extract calls inside method
                        for subnode in ast.walk(child):
                            if isinstance(subnode, ast.Call):
                                called_name = cls._get_call_name(subnode.func)
                                if called_name and called_name != child.name:
                                    relations.append(
                                        AstRelation(
                                            source_identifier=method_id,
                                            target_name=called_name,
                                            relation=RelationKind.CALLS,
                                            file_path=rel_path,
                                            line_number=subnode.lineno if hasattr(subnode, "lineno") else child.lineno,
                                        )
                                    )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Only top-level functions (not inside ClassDef)
                is_nested_in_class = any(
                    isinstance(parent, ast.ClassDef) and node in parent.body for parent in ast.walk(tree)
                )
                if not is_nested_in_class:
                    params = [arg.arg for arg in node.args.args]
                    doc = ast.get_docstring(node) or ""
                    sig = f"{node.name}({', '.join(params)})"
                    func_id = f"sym:{rel_path}:{node.name}"
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

                    # Extract calls inside function
                    for subnode in ast.walk(node):
                        if isinstance(subnode, ast.Call):
                            called_name = cls._get_call_name(subnode.func)
                            if called_name and called_name != node.name:
                                relations.append(
                                    AstRelation(
                                        source_identifier=func_id,
                                        target_name=called_name,
                                        relation=RelationKind.CALLS,
                                        file_path=rel_path,
                                        line_number=subnode.lineno if hasattr(subnode, "lineno") else node.lineno,
                                    )
                                )

                    # Check decorators for routes
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call):
                            dec_name = cls._get_call_name(dec.func)
                            if dec_name and any(r in dec_name.lower() for r in ["get", "post", "put", "delete", "route", "patch"]):
                                if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                                    route_path = dec.args[0].value
                                    verb = dec_name.split(".")[-1].upper()
                                    route_id = f"sym:{rel_path}:{verb} {route_path}"
                                    symbols.append(
                                        SymbolInfo(
                                            name=f"{verb} {route_path}",
                                            kind=SymbolKind.ROUTE,
                                            file_path=rel_path,
                                            start_line=node.lineno,
                                            end_line=getattr(node, "end_lineno", node.lineno),
                                            signature=f"{verb} {route_path} -> {node.name}",
                                        )
                                    )
                                    relations.append(
                                        AstRelation(
                                            source_identifier=route_id,
                                            target_name=node.name,
                                            relation=RelationKind.ROUTES_TO,
                                            file_path=rel_path,
                                            line_number=node.lineno,
                                        )
                                    )

        return symbols, relations

    @staticmethod
    def _get_call_name(node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None

    @classmethod
    def _parse_javascript_typescript(cls, content: str, rel_path: str) -> Tuple[List[SymbolInfo], List[AstRelation]]:
        symbols: List[SymbolInfo] = []
        relations: List[AstRelation] = []
        lines = content.splitlines()

        import_pat = re.compile(r'^\s*import\s+(?:(?:\*\s+as\s+[\w$]+|[\w$]+|\{[^}]+\})\s+from\s+)?[\'"]([^\'"]+)[\'"]')
        require_pat = re.compile(r'(?:const|let|var)\s+(?:[\w$]+|\{[^}]+\})\s*=\s*require\([\'"]([^\'"]+)[\'"]\)')
        class_pat = re.compile(r'^\s*(?:export\s+)?(?:default\s+)?class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$]+))?')
        func_pat = re.compile(r'^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(([^)]*)\)')
        arrow_pat = re.compile(r'^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>')
        interface_pat = re.compile(r'^\s*(?:export\s+)?interface\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$]+))?')
        route_pat = re.compile(r'(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*([A-Za-z0-9_$]+)?')
        call_pat = re.compile(r'\b([A-Za-z0-9_$]+)\s*\(')

        file_node_id = f"file:{rel_path}"

        for idx, line in enumerate(lines, 1):
            # Imports
            imp_m = import_pat.search(line) or require_pat.search(line)
            if imp_m:
                relations.append(
                    AstRelation(
                        source_identifier=file_node_id,
                        target_name=imp_m.group(1),
                        relation=RelationKind.IMPORTS,
                        file_path=rel_path,
                        line_number=idx,
                    )
                )

            # Class
            c_match = class_pat.search(line)
            if c_match:
                name = c_match.group(1)
                extends_name = c_match.group(2)
                class_id = f"sym:{rel_path}:{name}"
                symbols.append(
                    SymbolInfo(
                        name=name,
                        kind=SymbolKind.CLASS,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                    )
                )
                if extends_name:
                    relations.append(
                        AstRelation(
                            source_identifier=class_id,
                            target_name=extends_name,
                            relation=RelationKind.DEPENDS_ON,
                            file_path=rel_path,
                            line_number=idx,
                            properties={"type": "extends"},
                        )
                    )
                continue

            # Function
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

            # Arrow Component or Function
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

            # Interface
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

            # Express / Node Route
            r_match = route_pat.search(line)
            if r_match:
                verb = r_match.group(1).upper()
                route_path = r_match.group(2)
                handler = r_match.group(3)
                route_id = f"sym:{rel_path}:{verb} {route_path}"
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
                if handler:
                    relations.append(
                        AstRelation(
                            source_identifier=route_id,
                            target_name=handler,
                            relation=RelationKind.ROUTES_TO,
                            file_path=rel_path,
                            line_number=idx,
                        )
                    )

        return symbols, relations

    @classmethod
    def _parse_php(cls, content: str, rel_path: str) -> Tuple[List[SymbolInfo], List[AstRelation]]:
        symbols: List[SymbolInfo] = []
        relations: List[AstRelation] = []
        lines = content.splitlines()

        use_pat = re.compile(r'^\s*use\s+([^;]+);')
        class_pat = re.compile(r'^\s*(?:final\s+|abstract\s+)?class\s+([A-Za-z0-9_]+)(?:\s+extends\s+([A-Za-z0-9_]+))?(?:\s+implements\s+([^\{]+))?')
        func_pat = re.compile(r'^\s*(?:public|protected|private|static|\s)*function\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)')
        laravel_route_pat = re.compile(r'Route::(get|post|put|delete|patch|match|any)\s*\(\s*[\'"]([^\'"]+)[\'"](?:\s*,\s*(?:\[\s*([A-Za-z0-9_]+)::class\s*,\s*[\'"]([A-Za-z0-9_]+)[\'"]\s*\]|[\'"]([A-Za-z0-9_@]+)[\'"]))?')

        current_class: Optional[str] = None
        file_node_id = f"file:{rel_path}"

        for idx, line in enumerate(lines, 1):
            # Imports / Uses
            u_match = use_pat.search(line)
            if u_match:
                relations.append(
                    AstRelation(
                        source_identifier=file_node_id,
                        target_name=u_match.group(1).strip(),
                        relation=RelationKind.IMPORTS,
                        file_path=rel_path,
                        line_number=idx,
                    )
                )

            # Class
            c_match = class_pat.search(line)
            if c_match:
                current_class = c_match.group(1)
                extends_class = c_match.group(2)
                class_id = f"sym:{rel_path}:{current_class}"
                symbols.append(
                    SymbolInfo(
                        name=current_class,
                        kind=SymbolKind.CLASS,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                    )
                )
                if extends_class:
                    relations.append(
                        AstRelation(
                            source_identifier=class_id,
                            target_name=extends_class,
                            relation=RelationKind.DEPENDS_ON,
                            file_path=rel_path,
                            line_number=idx,
                            properties={"type": "extends"},
                        )
                    )
                continue

            # Method / Function
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

            # Laravel Route
            r_match = laravel_route_pat.search(line)
            if r_match:
                verb = r_match.group(1).upper()
                r_path = r_match.group(2)
                ctrl = r_match.group(3) or (r_match.group(5).split("@")[0] if r_match.group(5) else "")
                action = r_match.group(4) or (r_match.group(5).split("@")[1] if r_match.group(5) and "@" in r_match.group(5) else "")
                route_id = f"sym:{rel_path}:{verb} {r_path}"
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
                if ctrl:
                    target = f"{ctrl}@{action}" if action else ctrl
                    relations.append(
                        AstRelation(
                            source_identifier=route_id,
                            target_name=target,
                            relation=RelationKind.ROUTES_TO,
                            file_path=rel_path,
                            line_number=idx,
                        )
                    )

        return symbols, relations

    @classmethod
    def _parse_go(cls, content: str, rel_path: str) -> Tuple[List[SymbolInfo], List[AstRelation]]:
        symbols: List[SymbolInfo] = []
        relations: List[AstRelation] = []
        lines = content.splitlines()

        import_pat = re.compile(r'^\s*import\s+(?:\(\s*([^)]+)\s*\)|"([^"]+)")')
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

        return symbols, relations

    @classmethod
    def _parse_rust(cls, content: str, rel_path: str) -> Tuple[List[SymbolInfo], List[AstRelation]]:
        symbols: List[SymbolInfo] = []
        relations: List[AstRelation] = []
        lines = content.splitlines()
        fn_pat = re.compile(r'^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)')
        struct_pat = re.compile(r'^\s*(?:pub\s+)?(struct|enum|trait)\s+([A-Za-z0-9_]+)')
        use_pat = re.compile(r'^\s*use\s+([^;]+);')

        file_node_id = f"file:{rel_path}"

        for idx, line in enumerate(lines, 1):
            u_match = use_pat.search(line)
            if u_match:
                relations.append(
                    AstRelation(
                        source_identifier=file_node_id,
                        target_name=u_match.group(1).strip(),
                        relation=RelationKind.IMPORTS,
                        file_path=rel_path,
                        line_number=idx,
                    )
                )

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

        return symbols, relations

    @classmethod
    def _parse_c_family(cls, content: str, rel_path: str) -> Tuple[List[SymbolInfo], List[AstRelation]]:
        symbols: List[SymbolInfo] = []
        relations: List[AstRelation] = []
        lines = content.splitlines()
        using_pat = re.compile(r'^\s*(?:using|import)\s+([^;]+);')
        class_pat = re.compile(r'^\s*(?:public|private|protected|internal)?\s*(?:class|interface|record)\s+([A-Za-z0-9_]+)(?:\s*:\s*([A-Za-z0-9_,\s]+))?')
        method_pat = re.compile(r'^\s*(?:public|private|protected|static|\s)+[A-Za-z0-9_<>[\]]+\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*[{;]')

        file_node_id = f"file:{rel_path}"

        for idx, line in enumerate(lines, 1):
            u_match = using_pat.search(line)
            if u_match:
                relations.append(
                    AstRelation(
                        source_identifier=file_node_id,
                        target_name=u_match.group(1).strip(),
                        relation=RelationKind.IMPORTS,
                        file_path=rel_path,
                        line_number=idx,
                    )
                )

            c_match = class_pat.search(line)
            if c_match:
                name = c_match.group(1)
                bases = c_match.group(2)
                class_id = f"sym:{rel_path}:{name}"
                symbols.append(
                    SymbolInfo(
                        name=name,
                        kind=SymbolKind.CLASS,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                    )
                )
                if bases:
                    for b in bases.split(","):
                        b_clean = b.strip()
                        if b_clean:
                            relations.append(
                                AstRelation(
                                    source_identifier=class_id,
                                    target_name=b_clean,
                                    relation=RelationKind.DEPENDS_ON,
                                    file_path=rel_path,
                                    line_number=idx,
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

        return symbols, relations

    @classmethod
    def _parse_sql(cls, content: str, rel_path: str) -> Tuple[List[SymbolInfo], List[AstRelation]]:
        symbols: List[SymbolInfo] = []
        relations: List[AstRelation] = []
        lines = content.splitlines()
        table_pat = re.compile(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[`"\[]?)([A-Za-z0-9_]+)', re.IGNORECASE)
        fk_pat = re.compile(r'FOREIGN\s+KEY\s*.*?REFERENCES\s+[`"\[]?([A-Za-z0-9_]+)', re.IGNORECASE)

        current_table: Optional[str] = None

        for idx, line in enumerate(lines, 1):
            m = table_pat.search(line)
            if m:
                current_table = m.group(1)
                table_id = f"sym:{rel_path}:{current_table}"
                symbols.append(
                    SymbolInfo(
                        name=current_table,
                        kind=SymbolKind.DATABASE_TABLE,
                        file_path=rel_path,
                        start_line=idx,
                        end_line=idx,
                    )
                )
            if current_table:
                fk_m = fk_pat.search(line)
                if fk_m:
                    ref_table = fk_m.group(1)
                    relations.append(
                        AstRelation(
                            source_identifier=f"sym:{rel_path}:{current_table}",
                            target_name=ref_table,
                            relation=RelationKind.DEPENDS_ON,
                            file_path=rel_path,
                            line_number=idx,
                            properties={"type": "foreign_key"},
                        )
                    )

        return symbols, relations

    @classmethod
    def _parse_generic(cls, content: str, rel_path: str) -> List[SymbolInfo]:
        return []
