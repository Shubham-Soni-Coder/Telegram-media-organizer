import os
import time
import threading
from pathlib import Path
from queue import Queue, Empty
import mimetypes
import re
from folder_maker import FolderMaker

# =====================
# QUEUES & GLOBALS
# =====================
pending_q = Queue()  # files waiting to be checked
ready_q = Queue()  # files fully downloaded
seen_files = set()  # prevent duplicates
lock = threading.Lock()
DOWNLOAD_FOLDER = "D:/downloads/telegrzm download"
maker = FolderMaker("D:/")


# =====================
# FILE TYPE CHECKER
# =====================
def is_video_file(file_path: Path) -> bool:
    """
    Check if the file is a video file
    """
    VIDEO_EXTENSIONS = {
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".webm",
        ".flv",
        ".wmv",
        ".mpeg",
        ".mpg",
    }

    if not file_path.exists() or not file_path.is_file():
        return False

    # Extension check -> Fast
    if file_path.suffix.lower() in VIDEO_EXTENSIONS:
        return True

    # Mine type  checker -> slow
    mine_type, _ = mimetypes.guess_type(file_path)
    if mine_type and mine_type.startswith("video"):
        return True

    return False


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


# ============
# Procss Ready File
# ============


def process_ready_files():
    while True:
        try:
            path = ready_q.get(timeout=5)

            title = clean_filename(path)
            meida_type = maker.detect_media_type(title)

            if meida_type == "tv":
                target = maker.tv_target_path(path, title)
            else:
                target = maker.movie_target_path(path, title)

            maker.safe_move(path, target)

        except Empty:
            continue

        except Exception as e:
            print("[POST-PROCESS ERROR]", e)


# =====================
# PRODUCER
# =====================
def scan_folder(folder_path: str, interveal: int = 5):
    """
    Scan folder and enqueue the files only one

    """
    while True:
        try:
            for name in os.listdir(folder_path):
                file_path = Path(folder_path) / name
                if not file_path.is_file():
                    continue

                with lock:
                    if file_path not in seen_files:
                        seen_files.add(file_path)
                        pending_q.put(file_path)
                        print(f"[SCANNER] Added: {name}")

            time.sleep(interveal)
        except Exception as e:
            print(f"[SCANNER] Error: {e}")


# =====================
# CONSUMER
# =====================
def wait_until_stable(stable_check: int = 3, delay: int = 2):
    """
    Wait until the file is stable
    """
    while True:
        try:
            file_path = pending_q.get(timeout=5)

            if not file_path.exists():
                continue

            last_seen = -1
            stable_count = 0

            while stable_count < stable_check:
                current_size = file_path.stat().st_size

                if current_size == last_seen:
                    stable_count += 1

                else:
                    stable_count = 0

                last_seen = current_size
                time.sleep(delay)
            if is_video_file(file_path):
                ready_q.put(file_path)
                print(f"[STABLE] {file_path.name} is stable")
            else:
                print(f"[STABLE] {file_path.name} is not a video file")

        except Empty:
            continue
        except Exception as e:
            print(f"[STABLE] Error: {e}")


# =====================
# MAIN
# =====================
if __name__ == "__main__":

    producer = threading.Thread(
        target=scan_folder, args=(DOWNLOAD_FOLDER,), daemon=True
    )

    consumer = threading.Thread(target=wait_until_stable, daemon=True)

    post_processor = threading.Thread(target=process_ready_files, daemon=True)

    producer.start()
    consumer.start()
    post_processor.start()

    while True:
        time.sleep(1)

    # filename = Path("Fate Stay Night UBW - 22 [720p] [Dual] @Anime_Maniaac.mkv")
    # # filename = Path("Monster S1 - 02 [720p] [Dual] @Anime_Maniaac.mkv")
    # print(maker.parse_tv_title(clean_filename(filename)))
