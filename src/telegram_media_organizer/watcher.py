import os
import time
import threading
from pathlib import Path
from queue import Queue, Empty
import mimetypes
from telegram_media_organizer.organizer import FolderMaker
from telegram_media_organizer.cleaner import clean_filename


class DirectoryWatcher:
    def __init__(self, watch_folder: str, destination_folder: str):
        self.watch_folder = Path(watch_folder)
        self.maker = FolderMaker(destination_folder)

        # Queues
        self.pending_q = Queue()  # Detected files waiting for stability check
        self.ready_q = Queue()  # Stable files ready for processing

        # State
        self.seen_files = set()
        self.lock = threading.Lock()

        # Control
        self.running = False

    def start(self):
        self.running = True

        threads = [
            threading.Thread(target=self.scan_folder, daemon=True),
            threading.Thread(target=self.wait_until_stable, daemon=True),
            threading.Thread(target=self.process_ready_files, daemon=True),
        ]

        for t in threads:
            t.start()

        print(f"[WATCHER] Started watching {self.watch_folder}")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[WATCHER] Stopping...")
            self.running = False

    # =====================
    # PRODUCER
    # =====================
    def scan_folder(self, interval: int = 5):
        """
        Scan folder and enqueue new files
        """
        while self.running:
            try:
                if not self.watch_folder.exists():
                    time.sleep(interval)
                    continue

                for name in os.listdir(self.watch_folder):
                    file_path = self.watch_folder / name
                    if not file_path.is_file():
                        continue

                    with self.lock:
                        if file_path not in self.seen_files:
                            self.seen_files.add(file_path)
                            self.pending_q.put(file_path)
                            print(f"[SCANNER] Detected: {name}")

                time.sleep(interval)
            except Exception as e:
                print(f"[SCANNER] Error: {e}")
                time.sleep(interval)

    # =====================
    # CONSUMER 1: Stability Checker
    # =====================
    def wait_until_stable(self, stable_check: int = 3, delay: int = 2):
        """
        Wait until file size stops changing (download complete)
        """
        while self.running:
            try:
                file_path = self.pending_q.get(timeout=2)

                if not file_path.exists():
                    self.pending_q.task_done()
                    continue

                print(f"[STABILITY] Checking: {file_path.name}")

                last_seen = -1
                stable_count = 0

                # Check if file is still growing
                while stable_count < stable_check:
                    if not file_path.exists():
                        break

                    current_size = file_path.stat().st_size

                    if current_size == last_seen and current_size > 0:
                        stable_count += 1
                    else:
                        stable_count = 0

                    last_seen = current_size
                    time.sleep(delay)

                if not file_path.exists():
                    self.pending_q.task_done()
                    continue

                if is_video_file(file_path):
                    self.ready_q.put(file_path)
                    print(f"[STABLE] Ready: {file_path.name}")
                else:
                    print(f"[IGNORED] Not a video: {file_path.name}")

                self.pending_q.task_done()

            except Empty:
                continue
            except Exception as e:
                print(f"[STABILITY] Error: {e}")

    # =====================
    # CONSUMER 2: Processor
    # =====================
    def process_ready_files(self):
        while self.running:
            try:
                path = self.ready_q.get(timeout=2)

                if not path.exists():
                    self.ready_q.task_done()
                    continue

                print(f"[PROCESSING] {path.name}")

                title = clean_filename(path)
                media_type = self.maker.detect_media_type(title)

                if media_type == "tv":
                    target = self.maker.tv_target_path(path, title)
                else:
                    target = self.maker.movie_target_path(path, title)

                self.maker.safe_move(path, target)
                self.ready_q.task_done()

            except Empty:
                continue
            except Exception as e:
                print(f"[PROCESSOR] Error: {e}")


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
        ".ts",
    }

    if not file_path.exists() or not file_path.is_file():
        return False

    # Extension check -> Fast
    if file_path.suffix.lower() in VIDEO_EXTENSIONS:
        return True

    # Mime type checker -> Slow but more accurate
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith("video"):
            return True
    except Exception:
        pass

    return False
