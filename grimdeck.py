import zipfile
from datetime import datetime
import hashlib
import json
import platform
import os.path
import shutil
import sys
import tempfile

_CONFIG_FILE = 'config.json'


class Configuration:
    def __init__(self, save_dir, sync_path):
        self.save_dir = save_dir
        self.sync_path = sync_path

    def check(self):
        if not os.path.isdir(self.save_dir):
            raise IOError(f"Directory '{self.save_dir}' does not exist!")

        if not os.path.isdir(self.sync_path):
            raise IOError(f"Directory '{self.sync_path}' does not exist!")

    def do_sync(self):
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        hostname = platform.node()
        archive = f'save_{timestamp}_{hostname}.zip'
        filename = self._archive_directory(archive, self.save_dir)
        print(f"Created '{filename}'.")

        # checksum
        hash = hashlib.sha256()
        with open(filename, 'rb') as file:
            for block in iter(lambda: file.read(4096), b''):
                hash.update(block)

        hash_filename = os.path.splitext(filename)[0] + '.sha256'
        with open(hash_filename, 'w') as hash_file:
            hash_file.write(hash.hexdigest())
        print(f"Created checksum file '{hash_filename}'.")

        shutil.move(filename, self.sync_path)
        shutil.move(hash_filename, self.sync_path)
        print(f"Moved files to '{self.sync_path}'.")

    def _archive_directory(self, archive_filename, directory):
        rel_root = os.path.abspath(directory)

        with zipfile.ZipFile(archive_filename, 'w', zipfile.ZIP_STORED) as archive:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    abs_file = os.path.join(root, file)
                    if file.endswith('.bak'):
                        continue  # skip backup files (from Item Assistant?)
                    if os.path.isfile(abs_file):
                        archive_name = os.path.join(os.path.relpath(root, rel_root), file)
                    archive.write(abs_file, archive_name)
        return archive_filename


def parse_config_file():
    if not os.path.isfile(_CONFIG_FILE):
        return None

    with open(_CONFIG_FILE, 'r') as config_file:
        config = json.load(config_file)
        save_dir = config.get('save_dir', '')
        sync_path = config.get('sync_path', '')
        return Configuration(save_dir, sync_path)


def main():
    config = parse_config_file()
    if config is None:
        sys.exit(f"Configuration file '{_CONFIG_FILE}' could not be read.")

    config.check()
    config.do_sync()


if __name__ == '__main__':
    main()
