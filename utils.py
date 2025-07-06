import os, sys, shutil

def resource_path(rel: str) -> str:
    """Путь к файлу внутри пакета (работает как в IDE, так и из .exe)."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)

def ensure_data_dir(files, dst_folder="data"):
    """
    Создаёт dst_folder рядом с exe и копирует туда файлы,
    если папка ещё не существовала.
    """
    exe_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    target = os.path.join(exe_dir, dst_folder)

    if not os.path.exists(target):
        os.makedirs(target, exist_ok=True)
        for f in files:
            shutil.copy(resource_path(f), os.path.join(target, f))