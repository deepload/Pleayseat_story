#!/usr/bin/env python3
"""LE PROTOCOLE CLARA — relieur du roman (mise en page littéraire). HTML + PDF + EPUB."""
import os, subprocess
from pathlib import Path
import markdown2

BOOK_DIR = Path(__file__).parent
OUT_PDF  = BOOK_DIR / "Le_Protocole_Clara.pdf"
OUT_EPUB = BOOK_DIR / "Le_Protocole_Clara.epub"
OUT_HTML = BOOK_DIR / "Le_Protocole_Clara.html"

_CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
CHROME = next((p for p in _CHROME if os.path.exists(p)), _CHROME[0])

TITLE   = "Le Protocole Clara"
SERIES  = "Les Dossiers Delta — Livre Premier"
AUTHOR  = "deepload"
TAGLINE = "Il avait tout forcé. Pour la retrouver, il a dû construire quelque chose."
YEAR    = "2026"

ACTES = [
    ("Acte I — Genèse", ["ch01-genesis.md","ch02-the-world-that-took-her.md","ch03-claras-shield.md","ch04-the-vault.md","ch05-the-mirror.md","ch06-the-genome.md","ch07-the-family-answers.md","ch08-her-shadow-still-moves.md"]),
    ("Acte II — L'Enquête", ["ch09-the-diversion.md","ch10-roots.md","ch11-the-rails.md","ch12-war-gaming.md","ch13-breadcrumbs.md","ch14-trust-no-one.md","ch15-teaching-it-her.md","ch16-her-ghost.md","ch17-operation-starlight.md","ch18-the-case.md"]),
    ("Acte III — Le Compte à rebours", ["ch19-her-heartbeat.md","ch20-two-fires.md","ch21-the-skeleton.md","ch22-the-marketplace.md","ch23-the-mole.md","ch24-rehearsal.md","ch25-the-whole-picture.md"]),
    ("Acte IV — Avant", ["ch26-the-satellite-war.md","ch27-the-trust-machine.md","ch28-the-building.md","ch29-follow-the-money.md"]),
    ("Acte V — Le Protocole Clara", ["ch30-the-clara-protocol.md"]),
    ("Acte VI — La Longue Nuit", ["ch31-the-long-night-begins.md","ch32-reading-the-enemy.md","ch33-when-it-went-wrong-before.md","ch34-closing-the-loop.md","ch35-go-now.md"]),
    ("Acte VII — Le Prix", ["ch36-the-ministry.md","ch37-the-bank.md","ch38-what-it-costs.md"]),
    ("Acte VIII — La Traque", ["ch39-the-hunt.md","ch40-finding-the-secret.md"]),
    ("Acte IX — L'Aube", ["ch41-built-with-a-machine.md","ch42-the-choice.md","ch43-saving-clara.md"]),
]
CHAPTER_FILES = [f for _, files in ACTES for f in files]

def read(f):
    p = BOOK_DIR / f
    return p.read_text(encoding="utf-8") if p.exists() else None

def chap_title(t):
    for line in t.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return "Sans titre"

def md2html(t):
    return markdown2.markdown(t, extras=["fenced-code-blocks","tables","header-ids","cuddled-lists","strike"])

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap');
:root{ --ink:#1a1a1a; --soft:#555; --line:#d8d2c4; --paper:#fbf9f4; --accent:#7a1f2b; }
@page{ size:152mm 229mm; margin:20mm 18mm 18mm 18mm; @bottom-center{ content:counter(page); font-family:'EB Garamond',serif; font-size:9pt; color:#999; } }
@page :first{ margin:0; @bottom-center{content:none;} }
@page cover{ margin:0; @bottom-center{content:none;} }
*{ box-sizing:border-box; }
body{ font-family:'EB Garamond','Georgia',serif; font-size:11.5pt; line-height:1.62; color:var(--ink); background:var(--paper); }
.cover{ page:cover; page-break-after:always; height:229mm; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:0 22mm; background:linear-gradient(170deg,#0b0c10 0%,#15171f 45%,#241019 78%,#0b0c10 100%); color:#f4efe6; }
.cover .series{ letter-spacing:.45em; text-transform:uppercase; font-size:9pt; color:#c9a24b; margin-bottom:30mm; }
.cover h1{ font-family:'Cormorant Garamond',serif; font-weight:600; font-size:48pt; line-height:1.04; margin:0; }
.cover .rule{ width:54px; height:2px; background:#c9a24b; margin:14mm auto; }
.cover .tag{ font-family:'Cormorant Garamond',serif; font-style:italic; font-size:15pt; color:#d9cfc0; max-width:92mm; margin:0 auto; line-height:1.4; }
.cover .author{ position:absolute; bottom:24mm; letter-spacing:.3em; text-transform:uppercase; font-size:11pt; color:#efe7d8; }
.titlepage{ page:cover; page-break-after:always; height:229mm; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:0 24mm; }
.titlepage h1{ font-family:'Cormorant Garamond',serif; font-weight:600; font-size:34pt; margin:0 0 6mm; color:#111; }
.titlepage .series{ letter-spacing:.4em; text-transform:uppercase; font-size:8.5pt; color:var(--soft); }
.titlepage .tag{ font-style:italic; font-size:13pt; color:#444; margin-top:10mm; max-width:95mm; }
.titlepage .author{ margin-top:18mm; letter-spacing:.25em; text-transform:uppercase; font-size:10pt; color:#333; }
.titlepage .legal{ font-size:8pt; color:#999; margin-top:22mm; line-height:1.7; max-width:96mm; }
.toc{ page:cover; page-break-after:always; padding:24mm 6mm; }
.toc h2{ font-family:'Cormorant Garamond',serif; font-weight:600; font-size:26pt; text-align:center; margin:0 0 12mm; color:#111; }
.toc .act{ letter-spacing:.18em; text-transform:uppercase; font-size:9pt; color:var(--accent); margin:7mm 0 2mm; border-bottom:1px solid var(--line); padding-bottom:1.5mm; }
.toc .row{ font-size:10.5pt; color:#333; padding:1.2mm 0 1.2mm 6mm; }
.chapter{ page-break-before:always; }
.chapter h1{ font-family:'Cormorant Garamond',serif; font-weight:600; font-size:24pt; text-align:center; margin:14mm 0 10mm; color:#111; line-height:1.15; }
.chapter h2{ font-family:'Cormorant Garamond',serif; font-size:15pt; font-weight:600; color:#222; margin:8mm 0 3mm; }
p{ margin:0 0 2.6mm; text-align:justify; hyphens:auto; }
.chapter > p:first-of-type::first-letter{ font-family:'Cormorant Garamond',serif; font-size:300%; line-height:.9; float:left; padding:2px 6px 0 0; color:var(--accent); font-weight:600; }
em{ font-style:italic; } strong{ font-weight:600; }
hr{ border:none; text-align:center; margin:7mm 0; }
hr::after{ content:'\\2766'; color:var(--accent); font-size:13pt; letter-spacing:.4em; }
blockquote{ font-style:italic; color:#444; border-left:2px solid var(--line); margin:5mm 4mm; padding-left:5mm; }
pre{ display:none; }
"""

def build_html():
    titles = {f: chap_title(read(f)) for f in CHAPTER_FILES if read(f)}
    html = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><title>{TITLE}</title><style>{CSS}</style></head><body>
<div class="cover"><div class="series">{SERIES}</div><h1>{TITLE}</h1><div class="rule"></div><div class="tag">{TAGLINE}</div><div class="author">{AUTHOR}</div></div>
<div class="titlepage"><div class="series">{SERIES}</div><h1>{TITLE}</h1><div class="tag">{TAGLINE}</div><div class="author">{AUTHOR}</div>
<div class="legal">Roman. Ceci est une œuvre de fiction. Les noms, les personnages, les lieux et les événements sont le produit de l'imagination de l'auteur ou utilisés de manière fictive. Toute ressemblance avec des personnes ou des faits réels serait fortuite.<br><br>&copy; {YEAR} {AUTHOR}. Tous droits réservés.</div></div>
<div class="toc"><h2>Table des matières</h2>
"""
    for act, files in ACTES:
        html += f'<div class="act">{act}</div>\n'
        for f in files:
            if f in titles:
                html += f'<div class="row">{titles[f]}</div>\n'
    html += "</div>\n"
    for f in CHAPTER_FILES:
        md = read(f)
        if md:
            html += f'<div class="chapter">{md2html(md)}</div>\n'; print(f"  + {f}")
    html += "</body></html>"
    return html

def make_pdf(h):
    print("\n  Rendu PDF...")
    subprocess.run([CHROME,"--headless","--disable-gpu","--no-pdf-header-footer","--run-all-compositor-stages-before-draw","--virtual-time-budget=30000",f"--print-to-pdf={OUT_PDF}",str(h)], capture_output=True, text=True, timeout=300)
    return OUT_PDF.exists()

def make_epub():
    try: from ebooklib import epub
    except ImportError: print("  ebooklib absent"); return False
    book=epub.EpubBook(); book.set_identifier("le-protocole-clara-t1"); book.set_title(TITLE); book.set_language("fr"); book.add_author(AUTHOR); book.add_metadata("DC","description",TAGLINE)
    ecss=epub.EpubItem(uid="s",file_name="s.css",media_type="text/css",content=b"body{font-family:Georgia,serif;line-height:1.6;} h1{text-align:center;font-size:1.6em;margin:1.5em 0;} p{text-align:justify;text-indent:1.2em;margin:.2em 0;} hr{border:none;text-align:center;} hr:after{content:'\\2766';}")
    book.add_item(ecss); spine=["nav"]; toc=[]
    for f in CHAPTER_FILES:
        md=read(f)
        if md:
            c=epub.EpubHtml(title=chap_title(md), file_name=f.replace(".md",".xhtml").replace("-","_"), lang="fr"); c.content=md2html(md).encode(); c.add_item(ecss); book.add_item(c); spine.append(c); toc.append(c)
    book.toc=toc; book.spine=spine; book.add_item(epub.EpubNcx()); book.add_item(epub.EpubNav()); epub.write_epub(str(OUT_EPUB), book, {}); return OUT_EPUB.exists()

def main():
    print("="*60); print(f"  {TITLE} — {SERIES}"); print("="*60)
    have=[f for f in CHAPTER_FILES if (BOOK_DIR/f).exists()]
    print(f"  {len(have)}/{len(CHAPTER_FILES)} chapitres présents\n")
    OUT_HTML.write_text(build_html(), encoding="utf-8"); print(f"\n  HTML: {OUT_HTML}")
    print(f"  PDF:  {'OK' if make_pdf(OUT_HTML) else 'ÉCHEC'}")
    print(f"  EPUB: {'OK' if make_epub() else 'ÉCHEC'}")
    print("="*60)

if __name__=="__main__":
    main()
