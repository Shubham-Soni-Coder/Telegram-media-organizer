from telegram_media_organizer.watcher import DirectoryWatcher
from pathlib import Path

# Configuration
DOWNLOAD_FOLDER = "D:/downloads/telegrzm download"
DESTINATION_FOLDER = "D:/"


def main():
    # Create the download folder if it doesn't exist (simulated for safety)
    try:
        Path(DOWNLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    watcher = DirectoryWatcher(DOWNLOAD_FOLDER, DESTINATION_FOLDER)
    watcher.start()


if __name__ == "__main__":
    main()
