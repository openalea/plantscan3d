from pathlib import Path


def get_shared_data(file, share_path="data"):
    try:
        datadir = Path(__file__).parent / share_path
        return str(datadir / file)
    except:
        import os

        return os.getcwd()

