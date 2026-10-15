"""Render representative PDF pages and report basic structural checks."""
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / 'Rapport_Final_AuditHub.pdf'
OUT = ROOT / 'verification_pages'
OUT.mkdir(exist_ok=True)
document = fitz.open(PDF)
sample = sorted(set([0, 1, 2, 5, 10, 13, 14, 16, 18, 28, len(document) - 1]))
for index in sample:
    page = document[index]
    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.35, 1.35), alpha=False)
    pixmap.save(OUT / f'page-{index + 1:02d}.png')
text = '\n'.join(page.get_text() for page in document)
print(f'pages={len(document)}')
print(f'characters={len(text)}')
print(f'empty_pages={sum(not page.get_text().strip() for page in document)}')
print(f'red_template_marker={"EE0000" in text}')
print(f'placeholder_brackets={sum(text.count(token) for token in ("[Nom]", "[Date]", "[X]"))}')
print(f'chapter_count={sum(heading in text for heading in ("INFORMATIONS G\u00c9N\u00c9RALES", "OBJECTIFS DE L\u2019AUDIT", "P\u00c9RIM\u00c8TRE DE L\u2019AUDIT", "CRIT\u00c8RES D\u2019AUDIT", "\u00c9QUIPE D\u2019AUDIT", "M\u00c9THODOLOGIE D\u2019AUDIT", "D\u00c9ROULEMENT DE L\u2019AUDIT", "SYNTH\u00c8SE DES CONSTATATIONS", "NON-CONFORMIT\u00c9S D\u00c9TAILL\u00c9ES", "OBSERVATIONS ET OPPORTUNIT\u00c9S D\u2019AM\u00c9LIORATION", "CONCLUSION ET RECOMMANDATION DE CERTIFICATION", "ANNEXES"))}')
