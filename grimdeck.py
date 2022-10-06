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
    def __init__(self, save_dir, share_path):
        self.save_dir = save_dir
        self.share_path = share_path
        self.hostname = platform.node()

    def check(self):
        if not os.path.isdir(self.save_dir):
            raise IOError(f"Directory '{self.save_dir}' does not exist!")

        if not os.path.isdir(self.share_path):
            raise IOError(f"Directory '{self.share_path}' does not exist!")

    def _get_existing_files(self):
        end_pattern = f'_{self.hostname}.sha256'

        checksums_and_saves = {}
        for rel_file in os.listdir(self.share_path):
            if not rel_file.endswith(end_pattern):
                continue
            chk_file = os.path.join(self.share_path, rel_file)
            zip_file = os.path.splitext(chk_file)[0] + '.zip'

            if os.path.isfile(chk_file) and os.path.isfile(zip_file):
                with open(chk_file, 'r') as f:
                    hash = f.read().strip()
                checksums_and_saves[hash] = zip_file
        return checksums_and_saves

    def sync_to_share_path(self):
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        archive = f'save_{timestamp}_{self.hostname}.zip'
        current_save_file = self._archive_directory(archive, self.save_dir)
        print(f"Created '{current_save_file}'.")

        # checksum
        hash = hashlib.sha256()
        with open(current_save_file, 'rb') as file:
            for block in iter(lambda: file.read(4096), b''):
                hash.update(block)
        hash_str = hash.hexdigest()

        existing_saves = self._get_existing_files()
        identical_save = existing_saves.get(hash_str, None)

        if identical_save is not None:
            print(f'Synchronization skipped - file with this hash already exists: {identical_save}')
            os.remove(current_save_file)
            print(f"Deleted '{current_save_file}'.")
            return

        hash_filename = os.path.splitext(current_save_file)[0] + '.sha256'
        with open(hash_filename, 'w') as hash_file:
            hash_file.write(hash_str)
        print(f"Created checksum file '{hash_filename}'.")

        shutil.move(current_save_file, self.share_path)
        shutil.move(hash_filename, self.share_path)
        print(f"Moved files to '{self.share_path}'.")

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
        share_path = config.get('share_path', '')
        return Configuration(save_dir, share_path)


def main():
    config = parse_config_file()
    if config is None:
        sys.exit(f"Configuration file '{_CONFIG_FILE}' could not be read.")

    config.check()
    config.sync_to_share_path()


if __name__ == '__main__':
    main()
