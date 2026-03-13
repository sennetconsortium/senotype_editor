"""
add_terms.py

One-off script to populate retroactively terms into the senotype JSONs.
Initially, senotypes only contained codes, and terms were fetched for display in the
UI when the senotype was selected.

"""
import os
import configobj
import tqdm

from utils.configfile import ConfigFile
from tqdm import tqdm

def main():
    print('add_terms.py')

    # Get configuration information.
    # Assume
    cfgfile = '/Users/jas971/senotype-editor/app.cfg'
    cfg = ConfigFile(filename=cfgfile)

if __name__ == "__main__":
    main()