Pagewipe ePub DRM Remover ![GitHub All Releases](https://img.shields.io/github/downloads/C0m3b4ck/Pagewipe-ePub-DRM-Remover/total)
===

The script removes various manifestations of BooXtream's 'Social DRM' from ePub files. It is forked from <a href=https://github.com/grayleonard/booxtream-epub-drm-remover>Grayleonard's repo</a>. However, that has been abandoned and I have decided to remake it with support for Python3.

More from Grayleonard: 
["Identifying and Removing Verso/BooXtream 'Social DRM' EPUB eBook Watermarks"](https://pastebin.com/raw/E1xgCUmb)

The seven DRM watermarks that are removed are:
```
"WM0-2 are overt (readily visible) watermarks and are optional (meaning they may not necessarily be present):
  [WM0] -- Ex Libris Image Watermark
  [WM1] -- Disclaimer Page Watermark (via keywords)
  [WM2] -- Footer Watermarks
WM3-6 are covert (not readily visible) watermarks and are always present:
  [WM3] -- Filename Watermarks
  [WM4] -- Timestamp Fingerprinting
  [WM5] -- CSS Watermark
  [WM6] -- Image Metadata Watermarks"
```
# My additions
* Support for Python3
* Simpler instructions
* Support both for XML and HTML cleaning
* Support for config files
<b>Check out documentation.txt for more info!</b>

# Roadmap

* Add eBooks.de metadata removal (https://github.com/grayleonard/booxtream-epub-drm-remover/pull/9)
* <b>The Wordlist - get 5 words like "license", "is licensed to" and others that are common in eBooks of every country in the world. Please contribute any ones that you have to TheWordlist.txt and add in your language if it is not there already. <i>Please do not blindy translate, but use data from ebook research.</i></b>

# Installation

Read instructions.txt or read below:

**1. Make venv (for Python3, Python2 version might require manual lib downloads):**
<br>```python3 -m venv yourvenv```
<br>**2. Activate the venv:**
<br>```source yourvenv/bin/activate```
<br>**3. Run these commands:**
<br>```pip install --upgrade pip```
<br>```pip install -r requirements.txt```
<br>**4. Run the script:**
<br>```python3 cure_python3.py -i your_dirty_book.epub -o your_clean_book.epub```
<br>**5. Compare the dirty and clean version:**
<br>```./diff.sh your_dirty_book.epub your_clean_book.epub```
# Running
<br>Python2 version:
<br>```cure.py -i <infected .epub> -o <cleaned .epub output>```
<br>Python3 version:
<br>```python3 cure_python3.py -i <infected .epub> -o <cleaned .epub output> -c <configfile>```
