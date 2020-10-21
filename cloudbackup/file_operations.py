import os
import zipfile


def get_directory_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size


def zip_directory(directory, zip_name):
    with zipfile.ZipFile(zip_name + '.zip', 'w') as zf:
        for root, dirs, files in os.walk(directory):
            for file in files:
                zf.write(os.path.join(root, file))

    return zf


def get_file_metainf(self, filename, zip=False):
    if zip:
        zip_file = zip_directory(filename)
        file_size = os.path.getsize(zip_file)
    else:
        if os.path.isdir(filename):
            file_size = get_directory_size(filename)

