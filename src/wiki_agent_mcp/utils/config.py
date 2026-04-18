import os
import sys
from pathlib import Path

def get_data_root() -> Path:
    """Determine a writable directory for wiki data (database, cache)."""
    # 1. Environment variable (highest priority)
    env_dir = os.environ.get("WIKI_DATA_DIR")
    if env_dir:
        path = Path(env_dir)
        try:
            path.mkdir(parents=True, exist_ok=True)
            # Test writability
            test_file = path / ".write_test"
            test_file.touch()
            test_file.unlink()
            return path
        except Exception as e:
            print(f"WARNING: Cannot use WIKI_DATA_DIR={env_dir}: {e}", file=sys.stderr)
    
    # 2. User's Downloads folder
    downloads = Path.home() / "Downloads" / "wikis"
    try:
        downloads.mkdir(parents=True, exist_ok=True)
        test_file = downloads / ".write_test"
        test_file.touch()
        test_file.unlink()
        return downloads
    except Exception as e:
        print(f"WARNING: Cannot use Downloads folder: {e}", file=sys.stderr)
    
    # 3. AppData\Local (Windows) or ~/.local (Unix)
    appdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local")) / "wiki_mcp"
    try:
        appdata.mkdir(parents=True, exist_ok=True)
        test_file = appdata / ".write_test"
        test_file.touch()
        test_file.unlink()
        return appdata
    except Exception as e:
        print(f"WARNING: Cannot use AppData: {e}", file=sys.stderr)
    
    # 4. Temp directory (last resort)
    import tempfile
    temp_dir = Path(tempfile.gettempdir()) / "wiki_mcp_data"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir

DATA_ROOT = get_data_root()
DB_PATH = DATA_ROOT / "wiki_memory.db"
CACHE_DIR = DATA_ROOT / "wiki_cache"

def init_data_dirs():
    """Initialize data directories."""
    CACHE_DIR.mkdir(exist_ok=True)
    print(f"[wiki-agent] Data directory: {DATA_ROOT}", file=sys.stderr)
    print(f"[wiki-agent] Database path: {DB_PATH}", file=sys.stderr)
    sys.stderr.flush()
