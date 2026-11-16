"""Render/extract every physical page; preserve visual evidence coordinates."""
import argparse
import shutil
import sys
from pathlib import Path
from src.day7.data import ROOT, digest, write_json
from .common import DATA, SOURCE_ID


def ingest(source):
    try:
        import pymupdf
    except ImportError:
        # Optional local dependency folder; never changes the Day06 environment.
        sys.path.append(str(ROOT / '.bonus-deps'))
        import pymupdf
    from PIL import Image, ImageDraw
    DATA.mkdir(parents=True, exist_ok=True)
    target = DATA / 'source.pdf'
    if Path(source).resolve() != target.resolve():
        shutil.copyfile(source, target)
    doc = pymupdf.open(target)
    if len(doc) < 100:
        raise ValueError('Advanced source must contain at least 100 physical pages')
    images = DATA / 'pages'
    images.mkdir(exist_ok=True)
    rows = []
    for index, page in enumerate(doc):
        number = index + 1
        path = images / f'p{number:03}.jpg'
        # 1600px width makes small table/legend labels readable without giant PNGs.
        pix = page.get_pixmap(matrix=pymupdf.Matrix(1600 / page.rect.width, 1600 / page.rect.width), alpha=False)
        pix.save(str(path), jpg_quality=88)
        text = page.get_text(sort=True)
        rows.append({'page': number, 'source_id': SOURCE_ID, 'image': str(path.relative_to(ROOT)).replace('\\', '/'),
            'width_pt': page.rect.width, 'height_pt': page.rect.height,
            'text': text, 'text_chars': len(text.strip()), 'raster_image_count': len(page.get_images()),
            'coverage': 'rendered_full_page_and_extracted_text', 'page_sha256': digest(path)})
    write_json(DATA / 'pages.json', rows)
    original_manifest = __import__('json').loads((ROOT / 'data/day06/manifest.json').read_text(encoding='utf-8'))
    write_json(DATA / 'manifest.json', {**original_manifest, 'source_path_or_url': 'data/advanced/source.pdf',
        'day06_legacy_subset': {'content_page_count': original_manifest['content_page_count'], 'content_page_ids': original_manifest['content_page_ids']},
        'content_page_count': None, 'content_page_ids': 'Advanced coverage spans the entire 107-page PDF; use coverage.json for actual indexed/blank page status.',
        'page_counting_rule': 'Physical PDF pages 1 through 107 rendered and extracted; every useful nonblank page indexed, including appendices and references. Day06 80-page subset is retained only as provenance.',
        'physical_page_count': len(doc), 'source_sha256': digest(target),
        'coverage_policy': 'Render every physical page and extract all text, including front matter, appendices and references. Vision index records useful regions; blank/decorative pages explicitly classified, never used as informative image evidence.',
        'render': {'engine': 'PyMuPDF', 'version': pymupdf.VersionBind, 'width_px': 1600, 'jpg_quality': 88},
        'limitation': 'Vision descriptions are unverified machine extraction until checked against original rendered pages. No claim of perfect OCR or layout parsing.'})
    # Small contact sheets are navigation only, not evidence sent to the model.
    contact = ROOT / 'tmp/advanced'
    contact.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(rows), 24):
        sheet = Image.new('RGB', (1200, 1800), 'white')
        draw = ImageDraw.Draw(sheet)
        for n, row in enumerate(rows[start:start + 24]):
            img = Image.open(ROOT / row['image'])
            img.thumbnail((285, 265))
            x, y = (n % 4) * 300, (n // 4) * 300
            sheet.paste(img, (x, y + 25))
            draw.text((x + 10, y + 5), f"PDF page {row['page']}", fill='black')
        sheet.save(contact / f'contact-{start+1:03}.jpg', quality=90)
    print(f'Rendered/extracted {len(rows)} pages; source SHA256 {digest(target)}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    ingest(args.source)
