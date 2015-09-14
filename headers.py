import codecs
import csv
import fnmatch
import os
from bs4 import BeautifulSoup

TABLES_DIR = './export-data'

extract_header = lambda html: [
    h.get_text() for h in BeautifulSoup(
        html, 'html.parser').find('tr').findAll(['th', 'td'])
    if h.get_text()]


def find_files(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


unique_headers = set()
fnames = find_files(TABLES_DIR, '*.html')
with open('headers.csv', 'w') as fout:
    writer = csv.writer(fout)
    for fname in fnames:
        header = extract_header(codecs.open(fname, encoding='utf-8'))
        writer.writerow([cell.encode('utf-8') for cell in header])
        unique_headers.update([cell.strip() for cell in header])

with codecs.open('headers.txt', 'w', encoding='utf-8') as fout:
    fout.write('\n'.join(sorted(list(unique_headers))))
