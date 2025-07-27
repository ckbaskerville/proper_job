"""Logging configuration."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, List

from .constants import (
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    LOG_LEVEL,
    LOG_FILE,
    MAX_LOG_SIZE,
    LOG_BACKUP_COUNT
)
from .paths import PathConfig


def setup_logging(
        log_dir: Optional[Path] = None,
        log_level: Optional[str] = None,
        console_output: bool = True,
        file_output: bool = True
) -> None:
    """Setup application logging.

    Args:
        log_dir: Directory for log files
        log_level: Logging level
        console_output: Enable console output
        file_output: Enable file output
    """
    # Get paths
    paths = PathConfig()
    log_dir = log_dir or paths.logs_dir
    log_level = log_level or LOG_LEVEL

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if file_output:
        log_file_path = log_dir / LOG_FILE
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=MAX_LOG_SIZE,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(file_handler)

    # Configure third-party loggers
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    # Log startup
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized")
    logger.info(f"Log level: {log_level}")
    if file_output:
        logger.info(f"Log file: {log_file_path}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogManager:
    """Manages application logs."""

    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize log manager.

        Args:
            log_dir: Directory containing logs
        """
        paths = PathConfig()
        self.log_dir = log_dir or paths.logs_dir

    def get_log_files(self) -> List[Path]:
        """Get all log files.

        Returns:
            List of log file paths
        """
        if not self.log_dir.exists():
            return []

        # Get main log and rotated logs
        log_files = []
        for file in self.log_dir.iterdir():
            if file.name.startswith(LOG_FILE.split('.')[0]):
                log_files.append(file)

        return sorted(log_files, reverse=True)

    def get_log_size(self) -> int:
        """Get total size of all log files.

        Returns:
            Total size in bytes
        """
        total_size = 0
        for file in self.get_log_files():
            if file.exists():
                total_size += file.stat().st_size
        return total_size

    def clear_logs(self) -> int:
        """Clear all log files.

        Returns:
            Number of files deleted
        """
        count = 0
        for file in self.get_log_files():
            try:
                file.unlink()
                count += 1
            except Exception:
                pass
        return count

    def archive_logs(self, archive_path: Path) -> bool:
        """Archive log files to a zip file.

        Args:
            archive_path: Path for archive file

        Returns:
            True if successful
        """
        import zipfile

        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file in self.get_log_files():
                    if file.exists():
                        zf.write(file, file.name)
            return True
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to archive logs: {e}")
            return False