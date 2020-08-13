"""
get_clipboard_text(): Returns text in clipboard
"""
from __future__ import print_function
import random
import os
import platform
import re
import json
import string
import sys
from threading import Thread, BoundedSemaphore
import collections
import tkinter as tk
# from tkinter import ttk
import subprocess
from pathlib import Path
import warnings

import ffmpy
import requests
from bs4 import BeautifulSoup

class PopupWindow():
    def __init__(self, parent):
        self.win = None
        self.parent = parent
    def show(self):
        """ 
        Use this to show window
        Do not forget to override initContent first!
        """
        if self.win is None:
            self.initWin()
            self.initContent()
        self.win.lift()
        self.win.focus_force()
    def destroy(self, *_):
        """ To be called to dispose of the window """
        self.win.destroy()
        self.win = None
    def initWin(self):
        """ Initialise self.win and bind some keys and events """
        self.win = tk.Toplevel(self.parent)
        self.win.protocol("WM_DELETE_WINDOW", self.onclose)
        self.win.bind("<Escape>", self.onclose)
    def onclose(self, *_):
        """
        (To be overriden by inheritance)
        Called on X-button and Escape button
        """
        self.destroy() # <<< Do not forget this!
    def initContent(self):
        """
        (To be overriden by inheritance)
        Add widgets to self.win
        """
        raise NotImplementedError()

# PLATFORM SPECIFIC IMPLEMENTATIONS
if platform.system() == "Windows":
    # GET CLIPBOARD TEXT
    # https://stackoverflow.com/a/46133732/
    import ctypes
    import ctypes.wintypes as w

    CF_UNICODETEXT = 13

    U32 = ctypes.WinDLL('user32')
    K32 = ctypes.WinDLL('kernel32')

    OpenClipboard = U32.OpenClipboard
    OpenClipboard.argtypes = w.HWND,
    OpenClipboard.restype = w.BOOL
    GetClipboardData = U32.GetClipboardData
    GetClipboardData.argtypes = w.UINT,
    GetClipboardData.restype = w.HANDLE
    GlobalLock = K32.GlobalLock
    GlobalLock.argtypes = w.HGLOBAL,
    GlobalLock.restype = w.LPVOID
    GlobalUnlock = K32.GlobalUnlock
    GlobalUnlock.argtypes = w.HGLOBAL,
    GlobalUnlock.restype = w.BOOL
    CloseClipboard = U32.CloseClipboard
    CloseClipboard.argtypes = None
    CloseClipboard.restype = w.BOOL

    def get_clipboard_text():
        text = ""
        if OpenClipboard(None):
            h_clip_mem = GetClipboardData(CF_UNICODETEXT)
            text = ctypes.wstring_at(GlobalLock(h_clip_mem))
            GlobalUnlock(h_clip_mem)
            CloseClipboard()
        return text
    # END GET CLIPBOARD TEXT
    def getParser():
        return"html.parser"

    def open_file(path):
        os.startfile(path)

    def safeName(p):
        """ Returns filename that is safe for windows """
        for c in r"""\/:*?"<>|""":
            # occurences = findAll(c, p)
            # for i in reversed(occurences):
            #   del p[i]
            p = ''.join(p.split(c))
        return p
elif platform.system() == "Darwin": # Mac
    def get_clipboard_text():
        raise NotImplementedError()
    def getParser():
        raise NotImplementedError()
    def open_file(path):
        subprocess.Popen(["open", path])
    def safeName(*a):
        raise NotImplementedError("safeName on Mac")
elif platform.system() == "Unix-Linux":
    def get_clipboard_text():
        raise NotImplementedError()
    def getParser():
        raise NotImplementedError()
    def open_file(path):
        subprocess.Popen(["xdg-open", path])
    def safeName(*a):
        raise NotImplementedError("safeName on Linux")
else:
    def get_clipboard_text():
        raise NotImplementedError()
    def getParser():
        raise NotImplementedError()
    def open_file(path):
        raise NotImplementedError()
    def safeName(*a):
        raise NotImplementedError("safeName on Linux")

def load_cookie_manager_cookies(file_path):
    with file_path.open('r') as file_obj:
        return {c["name"]: c["value"] for c in json.load(file_obj)["cookies"]}

def getHeaders():
    return HEADERS

HEADERS_UA = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        + " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102"
        + " Safari/537.36 Edge/18.18363")
}

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", 
    "Accept-Encoding": "gzip, deflate", 
    "Accept-Language": "en-US", 
    "Dnt": "1", 
    "Upgrade-Insecure-Requests": "1", 
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363", 
}

class AutoSoupMixin(object):
    """docstring for AutoSoup"""
    def __init__(self, arg):
        super(AutoSoupMixin, self).__init__()
        self._url = None
        self._html = None
        self._soup = None
        self._session = None
    @property
    def url(self):
        if self._url is None:
            raise ValueError("No url set")
        return self._url
    @url.setter
    def url(self, url):
        self._url = url
        self._html = None
        self._soup = None
        self._session = None
    @property
    def session(self):
        if self._session is None:
            self._session = requests.Session()
        return self._session
    @session.setter
    def session(self, new_session):
        self._session = new_session
    @property
    def html(self):
        if self._html is None:
            self._html = get_html(url=self.url) if self._soup is None else self._soup.text
        return self._html
    @property
    def soup(self):
        if self._soup is None:
            self._soup = get_soup_from_html(self.html)
        return self._soup
    
        
class AutoSoup():
    def __init__(self, url, html=None, soup=None, session=None):
        self.url = url
        self._html = html
        self._soup = soup
        self._session = session
    @property
    def session(self):
        if self._session is None:
            self._session = requests.Session()
        return self._session
    @session.setter
    def session(self, new_session):
        self._session = new_session
    @property
    def html(self):
        if self._html is None:
            self._html = get_html(url=self.url) if self._soup is None else self._soup.text
        return self._html
    @property
    def soup(self):
        if self._soup is None:
            self._soup = get_soup_from_html(self.html)
        return self._soup

def getRandomFilepath(dirpath, allowed_chars=string.ascii_letters + string.digits, name_len=16):
    """
    Returns file path of non existing file with file name a random arrangement 
    from the passed allowed characters.
    """
    dir_proper_path = dirpath if isinstance(dirpath, Path) else Path(dirpath)
    if len(safeName(allowed_chars)) < len(allowed_chars):
        raise RuntimeError("Unsafe characters used for filename")
    while True:
        name = ''.join([random.choice(allowed_chars) for _ in range(name_len)])
        new_path = dir_proper_path / name
        if not new_path.exists():
            break
    return new_path

def findAll(p, s):
    return [m.start() for m in re.finditer(p, s)]

# TODO Remove
def getHtml(*a, **b): # pylint: disable=C0103
    warnings.warn("getHtml is deprecated, use get_html instead", DeprecationWarning, stacklevel=2)
    return get_html(*a, **b)

def getFilenameFromUrl(*a, **b):  # pylint: disable=C0103
    warnings.warn("getFilenameFromUrl is deprecated, use get_filename_from_url instead",
                  DeprecationWarning, stacklevel=2)
    return get_filename_from_url(*a, **b)

def getSoupFromHtml(*a, **b):  # pylint: disable=C0103
    warnings.warn("getSoupFromHtml is deprecated, use get_soup_from_html instead",
                  DeprecationWarning, stacklevel=2)    
    return get_soup_from_html(*a, **b)

def getSoup(*a, **b): # pylint: disable=C0103
    warnings.warn("getSoup is deprecated, use get_soup instead", DeprecationWarning, stacklevel=2)
    return get_soup(*a, **b)


def get_html(url, cookies=None, session=None, timeout=5, max_tries=5):
    """
    Exceptions possi    bly raised:
    requests.exceptions.ConnectionError
    requests.exceptions.Timeout
    """
    tries = 0
    success = False
    while tries < max_tries and not success:
        tries += 1
        try:
            params = {
                "headers": HEADERS,
                "timeout": timeout
            }
            if cookies is not None:
                params["cookies"] = cookies
            r = (session if session else requests).get(url, **params)
            success = True
        except requests.exceptions.MissingSchema:
            print("[ERROR]: Invalid url: {}".format(url), file=sys.stderr)
            raise
        except requests.exceptions.ConnectionError:
            if tries == 5:
                print("[ERROR]: There is a problem with the internet connection", file=sys.stderr)
                raise
        except requests.exceptions.Timeout:
            if tries == 5:
                print(f"[ERROR]: {url} timed out multiple times exceeding the maximum tries",
                      file=sys.stderr)
                raise
    if success and r.ok:
        return str(r.text)
    raise requests.exceptions.HTTPError(
            f"Invalid status code {r.status_code} while trying to access {url}"
        )

def resolve_redirect(url, cookies=None):
    r = requests.get(url, cookies=cookies)


def get_soup_from_html(html):
    return BeautifulSoup(html, getParser())

def get_soup(url, cookies=None, session=None):
    return get_soup_from_html(get_html(url, cookies=cookies, session=session))

def get_filename_from_url(url):
    if url[-1] == "/": url = url[:-1]
    n = url[url.rfind("/") + 1:]
    try:
        return n[:n.index("?")]
    except ValueError:
        return n

def download_hls_file(m3u8_url, file_path, exist_ok=False, cookies=None):
    if cookies:
        cookie_str = "Cookie: " + '; '.join([f"{k}={v}" for k, v in cookies.items()]) + r"\r\n"
    file_proper_path = Path(file_path)
    if file_proper_path.is_file():
        if exist_ok:
            return
        raise FileExistsError(file_path)
    file_proper_path.absolute().parent.mkdir(parents=True, exist_ok=True)
    ff = ffmpy.FFmpeg(
        inputs={m3u8_url: ["-headers", cookie_str] if cookies else None},
        outputs={str(file_proper_path): ["-c", "copy", "-bsf:a", "aac_adtstoasc"]}
    )
    # print(ff.cmd)
    ff.run()

def download_file(url, file_path, exist_ok=False, cookies=None, allow_redirects=True, session=None):
    # todo implement make_dirs as a named parameter to choose not to automatically make directories in case they don't exist
    file_path.absolute().parent.mkdir(parents=True, exist_ok=True)
    if file_path.is_file():
        if exist_ok:
            return
        raise FileExistsError(f"File {file_path} already exists")
    with (session if session else requests).get(url, headers=HEADERS, stream=True, timeout=5, cookies=cookies, allow_redirects=allow_redirects) as req: 
        if req.status_code != requests.codes.ok:
            raise requests.HTTPError(f"Request returned with status code {req.status_code}")
        # try:
        #     total_size = int(r.headers.get('content-length')) # in bytes
        # except TypeError:
        #     total_size = 1

        blocksize = 8096 # in bytes
        # bytes_downloaded = 0

        with file_path.open('wb') as file_obj:
            # shutil.copyfileobj(r.raw, f)
            for chunk in req.iter_content(chunk_size=blocksize):
                file_obj.write(chunk)
                # if _prog_func is not None:
                #     bytes_downloaded += blocksize
                #     perc_done = bytes_downloaded / total_size
                #     _prog_func(perc_done)

    # if os.path.getsize(filename) < total_size: # incomplete download
    #     print("Clearing up unfinished download", filename)
    #     os.remove(filename)

class DownloadThread(Thread):
    def __init__(self, url, dest_path, semaphore):
        super().__init__()
        self.url = url
        self.dest_path = dest_path
        self.semaphore = semaphore
    def run(self):
        with self.semaphore:
            download_file(self.url, self.dest_path)

class DownloadManager:
    """ Uses a single semaphore to manage multiple downloads """
    def __init__(self, worker_count):
        self.semy = BoundedSemaphore(value=worker_count)
        self.workers = []
    def has_alive(self):
        self.workers = [t for t in self.workers if t.is_alive()]
        return bool(self.workers)
    def add_thread(self, url, dest_path):
        thrd = DownloadThread(url, dest_path, self.semy)
        thrd.start()
        self.workers.append(thrd)

def dltofile(url, filename, prog_func=None, exist_ok=False, headers=None):
    # print("downloading",url)
    if prog_func is None:
        _prog_func = None
    else:
        _prog_func = prog_func
    dir_path = os.path.dirname(os.path.abspath(filename))
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)

    if os.path.isfile(filename):
        if exist_ok:
            return
        raise FileExistsError("File " + filename + " already exists") # file exists

    # r = requests.head(url, allow_redirects = False)
    with requests.get(url, headers=HEADERS, stream=True, timeout=5) as r: 
        if not r.ok:
            raise requests.HTTPError("Request returned with status code "+str(r.status_code))
        try:
            total_size = int(r.headers.get('content-length')) # in bytes
        except TypeError:
            total_size = 1

        blocksize = 8096 # in bytes
        bytes_downloaded = 0

        with open(filename, 'wb') as f:
            # shutil.copyfileobj(r.raw, f)
            for chunk in r.iter_content(chunk_size=blocksize):
                f.write(chunk)
                if _prog_func is not None:
                    bytes_downloaded += blocksize
                    perc_done = bytes_downloaded / total_size
                    _prog_func(perc_done)

    if os.path.getsize(filename) < total_size: # incomplete download
        print("Clearing up unfinished download", filename)
        os.remove(filename)

class FileDownloader:
    def __init__(self, url, dest=None, destDir=None, headers=None,
                 semaphore=None, exist_ok=False, prog_func=None, fnFromUrl=True):
        self.url = url
        self.dest = dest
        self.destDir = destDir
        self.headers = headers
        self.semaphore = semaphore
        self.exist_ok = exist_ok
        self.prog_func = prog_func
        self.shouldFnFromUrl = fnFromUrl

        if self.dest is None == self.destDir is None:
            raise RuntimeError("Dest and dest dir cannot be both blank")

        self.filepath = None
        self.done = False
        self.dlthread = None
    def isDone(self):
        if self.dlthread is None:
            return self.done
        return not self.dlthread.is_alive()
    def run(self):
        filepath = self.dest
        if self.dest is None:
            if self.shouldFnFromUrl:
                name = FileDownloader.removeInvalidChars(
                    FileDownloader.getFilenameFromUrl(self.url)
                )
                filepath = os.path.join(self.destDir, name)
            else:
                raise RuntimeError("Destination is a directory, enable filename"
                                   +" from URL to automatically get filename")
        else: # destDir is not None
            if os.path.isFile(self.destDir):
                raise FileExistsError("Destination folder is a file")

        if self.dest is not None and os.path.isfile(self.dest):
            if not self.exist_ok:
                raise FileExistsError(f"File {self.dest} already exists")
        else:
            if self.semaphore:
                with self.semaphore:
                    self.dlthread = Thread(
                        target=dltofile,
                        args=(
                            self.url,
                            filepath,
                            self.prog_func,
                            self.exist_ok,
                            self.headers
                        )
                    )
                    self.dlthread.start()
            else:
                dltofile(
                    self.url,
                    filepath,
                    self.prog_func,
                    self.exist_ok,
                    self.headers
                )
                self.done = True
        self.filepath = filepath
        return filepath
    def removeInvalidChars(filename):
        newfilename = ""
        for c in filename:
            if c in """\\/:*?"<>|""":
                newfilename += '_'
            else:
                newfilename += c
        return newfilename
    def getFilenameFromUrl(url):
        b = url.rfind('/') + 1
        e = url.find('?', b)
        if e == -1:
            e = len(url)
        return url[b:e]

class cesar: # pylint: disable=C0103
    """ Cesar's cipher """
    oa = ord('a')
    oA = ord('A')
    oz = ord('z')
    oZ = ord('Z')
    def chrMap(c, k):
        oc = ord(c)
        if oc >= cesar.oa and oc <= cesar.oz:
            new_c = chr((oc - cesar.oa + k) % 26 + cesar.oa)
        elif oc >= cesar.oA and oc <= cesar.oZ:
            new_c = chr((oc - cesar.oA + k) % 26 + cesar.oA)
        else:
            new_c = c
        return new_c
    def strMap(m, k):
        return ''.join((cesar.chrMap(c, k) for c in m))
    def __init__(self, m, k):
        self.new_m = cesar.strMap(m, k)
    def __str__(self):
        return self.new_m

def fact(num):
    """ Factorial of positive integers """
    if num < 0:
        raise ValueError("Cannot compute factorial of negative numbers")
    if num == 0:
        return 1
    prod = 1
    for i in range(2, num + 1):
        prod *= i
    return prod

def makeUnique(itrbl):
    """ Returns a list from the given list, where all elements are distinct. """
    return list(collections.OrderedDict.fromkeys(itrbl))
