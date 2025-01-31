#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import re

# Helper function to take a document and extract its title

def extract_title(doc_str):
    # The title is formatted as ".*\n=+\n\n"
    title = re.search(r'(.*)\n=+\n\n', doc_str)
    return (title[1], doc_str[title.end():])

# Change directory to the `pages` directory

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(f"{script_dir}/..")

# Clean the automatic directories

clean_dirs = [
    "public",
    "content/doc",
]
for directory in clean_dirs:
    if os.path.exists(directory):
        shutil.rmtree(directory)

# Import the documentation

# - 1) Each individual man page

man_pages = [entry.path for entry in os.scandir('../doc') if entry.is_file() and entry.name.endswith(('.1', '.3'))]
for file in man_pages:
    base = os.path.splitext(os.path.basename(file))[0]
    os.makedirs(f'content/doc/{base}', exist_ok=True)
    with open(file, 'r') as infile, open(f'content/doc/{base}/index.html', 'w') as outfile:
        outfile.write(f"""+++
title = "{base}"
aliases = ["/doc/html/{base}.html"]
+++

""")
        outfile.flush()
        subprocess.run(['perl', '../maint/132html', '-noheader', base], stdin=infile, stdout=outfile)

# - 2) The index page

with open('../doc/html/index.html', 'r') as doc_index:
    index_content = doc_index.read()
with open('content/doc/_index.md', 'w') as f:
    f.write("""+++
title = "Manual pages"
+++

<p>
The reference manual for PCRE2 consists of a number of pages that are listed
below in alphabetical order. If you are new to PCRE2, please read the first one
first.
</p>
""")

    # Extract both the tables from the input file
    tables = re.search(r'<table>.*</table>', index_content, re.DOTALL)
    f.write(tables[0] + "\n")

# Import the project pages

os.makedirs(f'content/project', exist_ok=True)
for file in ['AUTHORS.md', 'LICENCE.md', 'SECURITY.md']:
    with open(f'../{file}', 'r') as infile, open(f'content/project/{file}', 'w') as outfile:
        (title, content) = extract_title(infile.read())
        outfile.write(f"""+++
title = "{title}"
+++

{content}
""")

# Run commands to build site

base_url = None

if "CODESPACE_NAME" in os.environ and "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN" in os.environ:
    base_url = f"https://{os.environ['CODESPACE_NAME']}-1313.{os.environ['GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN']}/"
else:
    raise Exception("Environment variables CODESPACE_NAME and GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN are not set")

commands = [
    ["hugo", "-b", base_url],
    ["npx", "-y", "pagefind", "--site", "public"]
]

for command in commands:
    result = subprocess.run(command)
    if result.returncode != 0:
        raise Exception(f"Command '{command}' failed with exit code {result.returncode}")
