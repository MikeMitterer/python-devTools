"""Textkataloge wie bei agent-lessons: ein deutscher Katalog mit englischer msgid, vollständig
gegenüber dem Code, eindeutig, Merge ohne Konflikt; kein Oberflächentext ohne _()."""

import ast
import re
import shutil
import subprocess
from pathlib import Path

from babel.messages.extract import extract_from_dir
from babel.messages.pofile import read_po

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "mmit_devtools"
CATALOGS = {path.parts[-3]: path for path in PACKAGE.glob("locale/*/LC_MESSAGES/*.po")}
FIELDS = re.compile(r"\{(\w+)")


def identifiers(path: Path) -> list[str]:
    """Alle msgid einer .po-Datei in Dateireihenfolge, ohne den leeren Kopf."""
    return [m for m in re.findall(r'(?m)^msgid "(.*)"$', path.read_text(encoding="utf-8")) if m]


def catalog() -> dict:
    """Die Einträge des deutschen Katalogs je msgid."""
    with CATALOGS["de"].open("rb") as stream:
        return {message.id: message for message in read_po(stream) if message.id}


def used_messages() -> set[str]:
    """Alle Texte, die der Code mit _() markiert, wie pybabel extract sie findet."""
    found = extract_from_dir(PACKAGE, method_map=[("**.py", "python")], keywords={"_": None})
    return {message for _file, _line, message, _comments, _context in found}


def test_catalog_translates_every_text_of_the_code_once():
    """Nur ein deutscher Katalog; jeder Text des Codes hat genau einen nicht unscharfen Eintrag
    mit denselben Platzhaltern; jeder Eintrag hat ein Gegenstück im Code."""
    assert set(CATALOGS) == {"de"}
    # pybabel extract kennt nur _; ein Alias (import _ as text) entginge ihm.
    aliased = [
        f"{path.relative_to(ROOT)}:{node.lineno}"
        for path in sorted(PACKAGE.rglob("*.py"))
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.ImportFrom)
        and any(item.name == "_" and item.asname for item in node.names)
    ]
    assert not aliased, f"_ unter anderem Namen importiert: {aliased}"
    names = identifiers(CATALOGS["de"])
    doubled = sorted({name for name in names if names.count(name) > 1})
    assert not doubled, f"doppelt {doubled}"
    entries, found = catalog(), used_messages()
    assert not (missing := sorted(found - set(entries))), f"ohne Übersetzung: {missing}"
    assert not (orphaned := sorted(set(entries) - found)), f"verwaist: {orphaned}"
    fuzzy = sorted(name for name in found if entries[name].fuzzy or not entries[name].string)
    assert not fuzzy, f"unscharf oder leer: {fuzzy}"
    unequal = [
        name
        for name in found
        if sorted(FIELDS.findall(name)) != sorted(FIELDS.findall(entries[name].string))
    ]
    assert not unequal, f"andere Platzhalter: {unequal}"


def git(repo: Path, *args: str) -> None:
    """git im Test-Repo mit fester Identität."""
    identity = ["-c", "user.name=Test", "-c", "user.email=test@example.invalid"]
    subprocess.run(["git", "-C", str(repo), *identity, *args], check=True, capture_output=True)


def test_new_entries_from_two_branches_merge_without_conflict(tmp_path):
    """Zwei Branches hängen je einen Eintrag ans Ende: Mit .gitattributes geht der Merge glatt."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "master")
    shutil.copy(ROOT / ".gitattributes", repo / ".gitattributes")
    po = repo / "texte.po"
    po.write_text('msgid "a"\nmsgstr "A"\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "start")
    for branch, key in (("eins", "b"), ("zwei", "c")):
        git(repo, "switch", "-q", "-c", branch, "master")
        po.write_text(po.read_text() + f'\nmsgid "{key}"\nmsgstr "{key.upper()}"\n')
        git(repo, "commit", "-qam", key)
    git(repo, "switch", "-q", "master")
    git(repo, "merge", "-q", "--no-edit", "eins")
    git(repo, "merge", "-q", "--no-edit", "zwei")
    assert identifiers(po) == ["a", "b", "c"]


# Rohe Oberflächentexte: Literale in print() und write() mit Wörtern, und deutsche Literale
# außerhalb von _(). Docstrings zählen nicht.
WORDS = re.compile(r"[A-Za-zÄÖÜäöüß]{2,}")
OUTPUT_CALLS = {"print", "write"}


def german_words() -> re.Pattern:
    """Deutsch erkennen: Umlaute oder ein Wort, das nur in den deutschen Übersetzungen steht."""
    english, german = set(), set()
    for message in catalog().values():
        english.update(WORDS.findall(message.id))
        german.update(WORDS.findall(message.string or ""))
    only = sorted((word for word in german - english if not word.isupper()), key=len, reverse=True)
    return re.compile(r"[äöüÄÖÜß]|\b(" + "|".join(map(re.escape, only)) + r")\b")


def fixed_text(node: ast.AST) -> str:
    """Feste Teile eines Literals oder f-Strings; andere Ausdrücke ergeben einen leeren Text."""
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else ""
    if isinstance(node, ast.JoinedStr):
        return "".join(str(part.value) for part in node.values if isinstance(part, ast.Constant))
    return ""


def raw_texts(source: str, german: re.Pattern) -> list[str]:
    """Rohe Oberflächentexte eines Moduls, je mit ihren festen Teilen."""
    tree = ast.parse(source)
    skip = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr):
            skip.add(id(body[0].value))
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "_":
            skip.update(id(sub) for sub in ast.walk(node))
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            for arg in node.args if name in OUTPUT_CALLS else []:
                if id(arg) not in skip and WORDS.search(fixed_text(arg)):
                    found[id(arg)] = fixed_text(arg)
        if id(node) not in skip and german.search(fixed_text(node)):
            found[id(node)] = fixed_text(node)
            skip.update(id(sub) for sub in ast.walk(node))
    return sorted(found.values())


def test_no_raw_surface_texts():
    """Jeder Oberflächentext läuft über _(). Die Gegenprobe zeigt, dass ein roher Text in der
    Ausgabe und ein deutscher Text auffallen, ein übersetzter nicht."""
    german = german_words()
    probe = (
        'print("Done")\nprint(_("Done"))\nmessage = "Werkzeug fehlt"\n'
        'sys.stderr.write(f"  {text}\\n")\nlabel = f"Stand von {name}"\n'
    )
    assert raw_texts(probe, german) == ["Done", "Stand von ", "Werkzeug fehlt"]
    raw = {
        str(path.relative_to(ROOT)): texts
        for path in sorted(PACKAGE.rglob("*.py"))
        if (texts := raw_texts(path.read_text(encoding="utf-8"), german))
    }
    assert not raw, f"rohe Oberflächentexte: {raw}"
