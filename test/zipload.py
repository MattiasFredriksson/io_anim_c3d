import io
import os
import shutil
import tempfile
import urllib.request
import zipfile

TEST_FOLDER = os.path.join(tempfile.gettempdir(), 'io_anim_c3d', 'testfiles')
ZIPS = (
    ('https://www.c3d.org/data/Sample00.zip', 'sample00.zip'),
    ('https://www.c3d.org/data/Sample01.zip', 'sample01.zip'),
)


class Zipload:

    @staticmethod
    def download():
        if not os.path.isdir(TEST_FOLDER):
            os.makedirs(TEST_FOLDER)
        for url, target in ZIPS:
            fn = os.path.join(TEST_FOLDER, target)
            if not os.path.isfile(fn):
                print('Downloading: ', url)
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                                                                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                                         'Chrome/51.0.2704.103 Safari/537.36',
                                                           'Accept': 'text/html,application/xhtml+xml,application/xml;'
                                                                     'q=0.9,*/*;q=0.8'})
                with urllib.request.urlopen(req) as response, open(fn, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                print('... Complete')

    @staticmethod
    def extract(zf):
        out_path = os.path.join(TEST_FOLDER, os.path.basename(zf)[:-4])

        zip = zipfile.ZipFile(os.path.join(TEST_FOLDER, zf))
        # Loop equivalent to zip.extractall(out_path) but avoids overwriting files
        for zf in zip.namelist():
            fpath = os.path.join(out_path, zf)
            # If file already exist, don't extract
            if not os.path.isfile(fpath) and not os.path.isdir(fpath):
                print('Extracted:', fpath)
                zip.extract(zf, path=out_path)

    
    @staticmethod
    def download_and_extract():
        """ Download and extract all test files.
        """
        Zipload.download()
        for url, target in ZIPS:
            Zipload.extract(target)

    @staticmethod
    def get_compressed_filenames(zf) -> list[str]:
        """ Find all .c3d files in the specified .zip file.
        """
        with zipfile.ZipFile(os.path.join(TEST_FOLDER, zf)) as z:
            return [i for i in z.filelist
                    if i.filename.lower().endswith('.c3d')]

    @staticmethod
    def get_c3d_filenames(dn: str):
        """ Find and iterate all .c3d files in the specified folder.

        Args
        ----
        dn: Folder/directory name.
        """
        root_folder = os.path.join(TEST_FOLDER, dn)
        for root, dirs, files in os.walk(root_folder, topdown=False):
            for fn in files:
                if fn.endswith('.c3d'): 
                    yield os.path.join(root, fn)

    @staticmethod
    def get_c3d_path(*args):
        return os.path.join(TEST_FOLDER, *args)

    @staticmethod
    def read_c3d(zf: str, fn: str) -> io.BytesIO:
        """ Access a IO stream for the specified file in the .zip folder.

        Args
        ----
        zf: Name of the zipfile containing the file.
        fn: Filename to read within the zipfile.
        """
        with zipfile.ZipFile(os.path.join(TEST_FOLDER, zf)) as z:
            return io.BytesIO(z.open(fn).read())
