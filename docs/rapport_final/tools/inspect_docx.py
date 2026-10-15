"""Extract every paragraph/table run from a DOCX with its effective text colour."""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
DOCX = ROOT / "Structure rapport.docx"
OUT = Path(__file__).resolve().parents[1] / "template_analysis.txt"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def attr(node, name, default=""):
    return node.get(W + name, default) if node is not None else default


with ZipFile(DOCX) as archive:
    styles_root = ET.fromstring(archive.read("word/styles.xml"))
    styles = {}
    for style in styles_root.findall(f".//{W}style"):
        style_id = attr(style, "styleId")
        colour = style.find(f"{W}rPr/{W}color")
        styles[style_id] = attr(colour, "val", "AUTO").upper()

    parts = ["word/document.xml"]
    parts += sorted(name for name in archive.namelist() if name.startswith("word/header") and name.endswith(".xml"))
    parts += sorted(name for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
    lines = []
    for part in parts:
        root = ET.fromstring(archive.read(part))
        lines.append(f"===== {part} =====")
        for index, paragraph in enumerate(root.iter(W + "p"), 1):
            pstyle_node = paragraph.find(f"{W}pPr/{W}pStyle")
            pstyle = attr(pstyle_node, "val", "Normal")
            runs = []
            for run in paragraph.findall(f"{W}r"):
                text = "".join((node.text or "") for node in run.iter(W + "t"))
                if not text:
                    continue
                colour_node = run.find(f"{W}rPr/{W}color")
                colour = attr(colour_node, "val", styles.get(pstyle, "AUTO")).upper()
                runs.append(f"[{colour}] {text}")
            if runs:
                ancestry = "TABLE" if any(cell.find(f".//{W}p") is paragraph for cell in root.iter(W + "tc")) else "PARA"
                lines.append(f"{index:04d} {ancestry} style={pstyle}: " + " | ".join(runs))

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(OUT)
