"""Implement fixed-size and structure-aware chunking."""
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    """Split into deterministic character windows, retaining page metadata."""
    if size < 1 or overlap < 0 or overlap >= size:
        raise ValueError("Require size > 0 and 0 <= overlap < size")
    chunks, start = [], 0
    step = size - overlap
    while start < len(page.text):
        end = min(start + size, len(page.text))
        text = page.text[start:end].strip()
        if text:
            chunks.append(Chunk(f"{page.document_id}:{page.page}:fixed:{start}",
                                page.document_id, page.source, page.page, text,
                                {**page.metadata, "start_char": start, "end_char": end}))
        if end == len(page.text):
            break
        start += step
    return chunks


def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    """Pack extracted non-empty text lines up to max_size; split long lines safely."""
    if max_size < 1:
        raise ValueError("max_size must be positive")
    paragraphs, offset = [], 0
    for line in page.text.splitlines(keepends=True):
        content = line.strip()
        if content:
            start = offset + len(line) - len(line.lstrip())
            paragraphs.append((content, start, start + len(content)))
        offset += len(line)
    groups, current = [], None
    for para, para_start, _ in paragraphs:
        pieces = [(para[i:i + max_size], para_start + i,
                   para_start + i + len(para[i:i + max_size]))
                  for i in range(0, len(para), max_size)]
        for piece, piece_start, piece_end in pieces:
            candidate = f"{current[0]}\n\n{piece}" if current else piece
            if len(candidate) > max_size:
                groups.append(current)
                current = (piece, piece_start, piece_end)
            else:
                current = (candidate, current[1], piece_end) if current else (piece, piece_start, piece_end)
    if current:
        groups.append(current)
    return [Chunk(f"{page.document_id}:{page.page}:para:{i}", page.document_id,
                  page.source, page.page, text,
                  {**page.metadata, "segment": i, "start_char": start, "end_char": end})
            for i, (text, start, end) in enumerate(groups)]
