"""
One-shot wiki scraper (API-based, avoids 403 blocks).

Usage (from repo root):
    python -m rag.scrape

Fetches the curated list of One Piece wiki pages via MediaWiki API,
converts each to Markdown, and saves one .md file per page under backend/data/raw/.

Idempotent: already-fetched pages are skipped. Rate-limited to 1 request/sec.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
API_URL = "https://onepiece.fandom.com/api.php"
REQUEST_DELAY = 1.0  # seconds between requests

HEADERS = {
    "User-Agent": "op-companion-scraper/1.0 (educational RAG project; contact via GitHub)",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

# Same curated pages list
PAGES = [
    ("Monkey_D._Luffy", "luffy"),
    ("Roronoa_Zoro", "zoro"),
    ("Nami", "nami"),
    ("Usopp", "usopp"),
    ("Vinsmoke_Sanji", "sanji"),
    ("Tony_Tony_Chopper", "chopper"),
    ("Nico_Robin", "robin"),
    ("Franky", "franky"),
    ("Brook", "brook"),
    ("Jinbe", "jinbe"),
    ("Silvers_Rayleigh", "rayleigh"),
    ("Monkey_D._Garp", "garp"),
    ("Sabo", "sabo"),
    ("Portgas_D._Ace", "ace"),
    ("Shanks", "shanks"),
    ("Edward_Newgate", "whitebeard"),
    ("Charlotte_Linlin", "big_mom"),
    ("Kaido", "kaido"),
    ("Marshall_D._Teach", "blackbeard"),
    ("Crocodile", "crocodile"),
    ("Donquixote_Doflamingo", "doflamingo"),
    ("Rob_Lucci", "rob_lucci"),
    ("Trafalgar_D._Water_Law", "law"),
    ("Eustass_Kid", "kid"),
    ("Im", "im"),
    ("Imu", "imu"),
    ("Five_Elders", "five_elders"),
    ("Vegapunk", "vegapunk"),
    ("Cipher_Pol", "cipher_pol"),
    ("Gol_D._Roger", "roger"),
    ("Joy_Boy", "joy_boy"),
    ("Void_Century", "void_century"),
    ("Will_of_D.", "will_of_d"),
    ("Ancient_Weapons", "ancient_weapons"),
    ("Poneglyph", "poneglyph"),
    ("Laugh_Tale", "laugh_tale"),
    ("Devil_Fruit", "devil_fruit"),
    ("Gomu_Gomu_no_Mi", "gomu_gomu"),
    ("Hito_Hito_no_Mi,_Model:_Nika", "nika_fruit"),
    ("Mera_Mera_no_Mi", "mera_mera"),
    ("Yami_Yami_no_Mi", "yami_yami"),
    ("Gura_Gura_no_Mi", "gura_gura"),
    ("Ope_Ope_no_Mi", "ope_ope"),
    ("Hana_Hana_no_Mi", "hana_hana"),
    ("Magu_Magu_no_Mi", "magu_magu"),
    ("Pika_Pika_no_Mi", "pika_pika"),
    ("Tori_Tori_no_Mi,_Model:_Phoenix", "marco_fruit"),
    ("Soru_Soru_no_Mi", "soru_soru"),
    ("Logia", "logia"),
    ("Zoan", "zoan"),
    ("Paramecia", "paramecia"),
    ("Haki", "haki"),
    ("Haoshoku_Haki", "conquerors_haki"),
    ("Kenbunshoku_Haki", "observation_haki"),
    ("Busoshoku_Haki", "armament_haki"),
    ("Bounty", "bounty"),
    ("Four_Emperors", "four_emperors"),
    ("Seven_Warlords_of_the_Sea", "warlords"),
    ("Marines", "marines"),
    ("World_Government", "world_government"),
    ("Grand_Line", "grand_line"),
    ("New_World", "new_world"),
    ("One_Piece_(Manga)", "one_piece_overview"),
    ("Straw_Hat_Pirates", "straw_hat_pirates"),
    ("Alabasta_Arc", "arc_alabasta"),
    ("Enies_Lobby_Arc", "arc_enies_lobby"),
    ("Marineford_Arc", "arc_marineford"),
    ("Dressrosa_Arc", "arc_dressrosa"),
    ("Whole_Cake_Island_Arc", "arc_whole_cake"),
    ("Wano_Country_Arc", "arc_wano"),
    ("Egghead_Arc", "arc_egghead"),
]


def slug_to_title(slug: str) -> str:
    """Convert wiki slug to proper MediaWiki title."""
    return slug.replace("_", " ")


def fetch_page_html(title: str, client: httpx.Client) -> str:
    """Fetch parsed HTML via MediaWiki API."""
    params = {
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json",
        "formatversion": "2",
        "redirects": "1",
    }

    response = client.get(API_URL, params=params, headers=HEADERS, timeout=20)
    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise ValueError(f"API error for {title}: {data['error']}")

    return data["parse"]["text"]


def extract_main_content(html: str, page_title: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Remove noisy elements
    for tag in soup.select(
        "aside, .navbox, .toc, script, style, .mw-editsection, "
        ".reference, sup.reference, .thumb, .gallery, "
        "footer, header, nav"
    ):
        tag.decompose()

    content_div = soup.find("div", class_="mw-parser-output")
    if not content_div:
        content_div = soup

    md = markdownify(str(content_div), heading_style="ATX", bullets="-")

    return f"# {page_title}\n\n{md.strip()}\n"


def scrape_page(slug: str, output_stem: str, client: httpx.Client) -> bool:
    out_path = RAW_DIR / f"{output_stem}.md"

    if out_path.exists():
        print(f"  skip  {output_stem}")
        return False

    title = slug_to_title(slug)

    try:
        html = fetch_page_html(title, client)
    except Exception as exc:
        print(f"  ERROR {output_stem}: {exc}")
        return False

    md_content = extract_main_content(html, title)
    out_path.write_text(md_content, encoding="utf-8")

    print(f"  fetch {output_stem} ({len(md_content):,} chars)")
    return True


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Saving pages to: {RAW_DIR}\n")

    fetched = 0
    skipped = 0

    with httpx.Client() as client:
        for i, (slug, stem) in enumerate(PAGES):
            if scrape_page(slug, stem, client):
                fetched += 1
                if i < len(PAGES) - 1:
                    time.sleep(REQUEST_DELAY)
            else:
                skipped += 1

    print(f"\nDone. Fetched: {fetched}, Skipped: {skipped}, Total: {fetched + skipped}")


if __name__ == "__main__":
    main()