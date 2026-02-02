import re
from pathlib import Path


# =====================
# CLEAN FILENAME
# =====================
def clean_filename(file_path: Path) -> str:
    """
    Clean filename for movies, TV shows, and anime.
    Assumes file is a validated video.
    """

    stem = file_path.stem

    # Remove bracket junk: [720p], [Dual], etc.
    stem = re.sub(r"\[.*?\]", "", stem)
    stem = re.sub(r"\(.*?\)", "", stem)

    # Remove unclosed brackets/parenthesis at the end (e.g. "[H_1" -> "")
    stem = re.sub(r"\[[^\]]*$", "", stem)
    stem = re.sub(r"\([^\)]*$", "", stem)

    # Remove @channel names
    stem = re.sub(r"@\w+", "", stem)

    # Normalize separators
    stem = re.sub(r"[._]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip()

    # TV / Anime patterns (in priority order)

    # S01E02, S1E2, S1 02
    tv_match = re.search(r"(.*?)(S\d+\s*E?\d+)", stem, re.IGNORECASE)
    if tv_match:
        return tv_match.group(1).strip() + " " + tv_match.group(2).upper()

    # Anime style: "Title - 22"
    anime_match = re.search(r"(.*?)[\s\-]+(\d{1,3})$", stem)
    if anime_match:
        title = anime_match.group(1).strip()
        episode = anime_match.group(2)
        return f"{title} E{episode}"

    # Movie with year
    movie_match = re.search(r"(.*?\b(19|20)\d{2}\b)", stem)
    if movie_match:
        return movie_match.group(1).strip()

    # Fallback
    return stem
