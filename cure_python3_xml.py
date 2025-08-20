import os
import shutil
import sys, getopt
import zipfile
import hashlib
import json
from bs4 import BeautifulSoup as bs
from wand.image import Image

baseUrl = ".tmp/"
prefix = ""

# Default options, can be overridden by config file
options = {
    "disclaimer_keywords": ["disclaimer"],
    "exlibris_keywords": ["exlibrispage", "exlibris"],
    "footer_keywords": ["is licensed to"],
    "css_watermark_keyword": "boekstaaf",
}

def load_config(path):
    global options
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        options.update(config_data)
        print(f'[Config] Loaded configuration from {path}')
    except Exception as e:
        print(f'[Config] Failed to load config {path}: {e}')
        sys.exit(1)

def parse_xml_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return bs(content, "lxml-xml")

def parse_html_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return bs(content, "html.parser")

def wm0(entry):
    global prefix
    print('\n\n === Removing \'Ex Libris\' watermark (WM0) === \n\n')

    print(entry)
    if "/" in entry:
        prefix = os.path.join(entry.split("/")[0])

    soup = parse_xml_file(entry)

    for keyword in options["exlibris_keywords"]:
        exlibrispage = soup.find("item", id=keyword)
        print(exlibrispage)
        if exlibrispage is not None:
            exlibrispage_filename = dict(exlibrispage.attrs)['href']
            try:
                os.remove(os.path.join(prefix, exlibrispage_filename))
            except FileNotFoundError:
                pass
            references = searchDirectoryForString('.', keyword)
            for reference in references:
                soup_ref, tags = findAttrInFile(reference, keyword, xml=True)
                removeTagsFromFile(reference, soup_ref, tags)
        else:
            print(f'\n{keyword} watermark not found')

    # Additionally remove BooXtream tags
    for keyword in ["BooXtream"]:
        references = searchDirectoryForString('.', keyword)
        for reference in references:
            soup_ref, tags = findAttrInFile(reference, keyword, xml=True)
            removeTagsFromFile(reference, soup_ref, tags)

    print('\nOK')

def wm1():
    global prefix
    print('\n\n === Removing \'Disclaimer\' watermark (WM1) === \n\n')
    disclaimer_files = set()
    candidate_keywords = [k.lower() for k in options["disclaimer_keywords"]]
    
    # Find files by filename keyword
    for root, dirnames, filenames in os.walk("."):
        for filename in filenames:
            for keyword in candidate_keywords:
                if keyword in filename.lower():
                    disclaimer_files.add(os.path.join(root, filename))
    
    # Find files containing disclaimer keywords in content
    for root, dirnames, filenames in os.walk("."):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    text = f.read().lower()
                    if any(k in text for k in candidate_keywords):
                        disclaimer_files.add(full_path)
            except Exception:
                pass
    
    if not disclaimer_files:
        print('\nNo Disclaimer file found')
        return
    
    for disclaimer in disclaimer_files:
        print(f"[wm1] Removing disclaimer file: {disclaimer}")
        references = searchDirectoryForString('.', os.path.basename(disclaimer))
        for reference in references:
            soup_ref, tags = findAttrInFile(reference, os.path.basename(disclaimer), xml=True)
            removeTagsFromFile(reference, soup_ref, tags)
        try:
            os.remove(disclaimer)
        except FileNotFoundError:
            pass
    print('\nOK')

def wm2():
    global prefix
    print('\n\n === Removing \'licensing\' watermark (WM2) === \n\n')
    for keyword in options["footer_keywords"]:
        references = searchDirectoryForString('.', keyword)
        for reference in references:
            soup_ref, tags = findTagsInFile(reference, xml=False)  # HTML files
            for tag in tags:
                if len(tag.findChildren()) == 0:  # No <p> with other <p> inside them
                    if keyword in str(tag):
                        print(f"Found match in file: {tag}")
                        removeTagFromFile(reference, soup_ref, tag)
    print('\nOK')

def wm3(entry):
    global prefix
    print('\n\n === Removing \'filename\' watermark (WM3) === \n\n')
    soup = parse_xml_file(entry)
    items = soup.findAll("item")
    for item in items:
        rand_name = deterministicNameGen()
        href = dict(item.attrs)['href']
        filetype = href.split('.')[-1]
        rand_name += '.'
        rand_name += filetype
        href_path = ""
        if "/" in href:
            href_path = '/'.join(href.split("/")[:-1])
            href = ''.join(href.split("/")[-1])
        new_url = os.path.join(href_path, rand_name)
        print(f'[wm3] Renaming {href} to {new_url}')
        references = searchDirectoryForString('.', href)
        for reference in references:
            replaceStringInFile(reference, href.split("/")[-1], rand_name.split("/")[-1])
        renameFile(os.path.join(prefix, href_path, href), os.path.join(prefix, href_path, rand_name))
    print('\nOK')

def wm4():
    print('\n\n === Removing \'timestamp\' watermark (WM4) === \n\n')
    # Timestamp WM - taken care of when unzipping / repackaging :-)
    print('\nOK')

def wm5():
    global prefix
    print('\n\n === Removing \'boekstaaf\' watermark (WM5) === \n\n')
    css_path = ""
    for root, dirnames, filenames in os.walk("."):
        for filename in filenames:
            if filename.lower().endswith(".css"):
                print(f"[wm5] Found CSS file: {filename}")
                css_path = os.path.join(root, filename)
    if css_path == "":
        print("No CSS file found for WM5")
        return
    with open(css_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open(css_path, "w", encoding="utf-8") as f:
        for line in lines:
            if options["css_watermark_keyword"] not in line:
                f.write(line)
    print('\nOK')

def wm6():
    print('\n\n === Removing \'exif\' watermark (WM6) === \n\n')
    jpg_paths = []
    png_paths = []
    for root, dirnames, filenames in os.walk("."):
        for filename in filenames:
            if filename.lower().endswith(".jpg"):
                print(f"[wm6] Found jpg file: {filename}")
                jpg_paths.append(os.path.join(root, filename))
            if filename.lower().endswith(".png"):
                print(f"[wm6] Found png file: {filename}")
                png_paths.append(os.path.join(root, filename))
    for path in jpg_paths:
        print(f"[wm6] Removing exif from {path}")
        with Image(filename=path) as img:
            img.strip()
            img.save(filename=path)
    for path in png_paths:
        print(f"[wm6] Removing metadata from {path}")
        with Image(filename=path) as img:
            img.strip()
            img.save(filename=path)
    print('\nOK')

idx = 0
def deterministicNameGen():
    string = '''We need to take information, wherever it is stored, make our copies and share them with
    the world. We need to take stuff that's out of copyright and add it to the archive. We need
    to buy secret databases and put them on the Web. We need to download scientific
    journals and upload them to file sharing networks. We need to fight for Guerilla Open
    Access.

    With enough of us, around the world, we'll not just send a strong message opposing the
    privatization of knowledge - we'll make it a thing of the past. Will you join us?

    Aaron Swartz
    July 2008, Eremo, Italy
    '''
    global idx
    m = hashlib.md5()
    m.update((string + str(idx)).encode('utf-8'))
    idx += 1
    return m.hexdigest()[0:20]


def searchDirectoryForString(path, match):
    found = []
    print(f'[searchDirectoryForString] Searching {path} for {match}')
    for path, dirs, files in os.walk(path):
        for file in files:
            fullpath = os.path.join(path, file)
            try:
                with open(fullpath, 'r', encoding='utf-8') as f:
                    contents = f.read()
                if str(match) in contents:
                    print(f'[searchDirectoryForString] Found match in file {fullpath}')
                    found.append(fullpath)
            except Exception:
                continue
    return found

def replaceStringInFile(path, match, replace):
    print(f'[replaceStringInFile] Replacing {match} with {replace} in {path}')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            fdata = f.read()
        fdata = fdata.replace(match, replace)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(fdata)
    except Exception as e:
        print(f"Error replacing string in file {path}: {e}")

def renameFile(path, dst):
    print(f'[renameFile] Renaming {path} to {dst}')
    try:
        os.rename(path, dst)
    except Exception as e:
        print(f"Error renaming file {path} to {dst}: {e}")

def findTagsInFile(path, tag="", xml=False):
    soup = parse_xml_file(path) if xml else parse_html_file(path)
    tags = soup.find_all(tag) if tag else soup.find_all()
    return soup, tags

def findAttrInFile(path, match, xml=False):
    soup = parse_xml_file(path) if xml else parse_html_file(path)
    tags = []
    for tag in soup.find_all():
        attrs = dict(tag.attrs)
        if match in str(attrs):
            print(f'[findAttrInFile] Found match in {tag}')
            tags.append(tag)
    return soup, tags

def removeTagFromFile(path, soup, tag):
    print(f'[removeTagFromFile] Removing {tag} from {path}')
    tag.extract()
    with open(path, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

def removeTagsFromFile(path, soup, tags):
    print(f'[removeTagsFromFile] Removing {tags} from {path}')
    for tag in tags:
        tag.extract()
    with open(path, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

def parseContainer():
    container = "META-INF/container.xml"
    soup = parse_xml_file(container)
    rootfile = soup.find('rootfile')
    path = dict(rootfile.attrs)['full-path']
    print(f'[parseContainer] Found entrypoint to ePub: {path}')
    return path

def extract(path):
    tmp = zipfile.ZipFile(path)
    tmp.extractall(baseUrl)

def writeToFile(path, content):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    with open(path, "w", encoding='utf-8') as f:
        f.write(content)

def buildEpub(path):
    print('\n\n === Rebuilding ePub === \n\n')
    os.chdir("../")
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    build = zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED)
    os.chdir(baseUrl)
    print('[buildEpub] Adding mimetype to ePub ...')
    build.write("mimetype")
    for root, dirs, files in os.walk("."):
        for file in files:
            if "mimetype" not in file:
                filepath = os.path.join(root, file)
                print(f'[buildEpub] Writing {filepath} to ePub ...')
                zpth = filepath[len(".")+len(os.sep):]
                build.write(filepath, zpth)
    os.chdir("..")
    build.close()

def clean():
    print('[clean] Cleaning temporary directory ...')
    shutil.rmtree(baseUrl)

def main(argv):
    infected = ''
    output = ''
    config_path = None

    try:
        opts, args = getopt.getopt(argv,"hi:o:c:", ["in=", "out=", "config="])
    except getopt.GetoptError:
        print('Usage: cure.py -i <infected.epub> -o <output.epub> [-c <config.json>]')
        sys.exit(2)
    if len(opts) == 0:
        print('Usage: cure.py -i <infected.epub> -o <output.epub> [-c <config.json>]')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('Usage: cure.py -i <infected.epub> -o <output.epub> [-c <config.json>]')
            sys.exit()
        elif opt in ("-i", "--in"):
            infected = arg
        elif opt in ("-o", "--out"):
            output = arg
        elif opt in ("-c", "--config"):
            config_path = arg

    if config_path:
        load_config(config_path)

    print(f'Curing {infected} ...')
    extract(infected)
    os.chdir(baseUrl)
    entry = parseContainer()
    wm0(entry)
    wm1()
    wm2()
    wm3(entry)
    wm4()
    wm5()
    wm6()
    buildEpub(output)
    clean()

if __name__ == "__main__":
    main(sys.argv[1:])
