#!/usr/bin/python3

# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2021 Yorik van Havre <yorik@uncreated.net>              *
# *                 2025 SargoDevel <sargo-devel@o2.pl>                     *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Library General Public License (LGPL)   *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************
# ***************************************************************************
# *                                                                         *
# *   Original code modified by: SargoDevel <sargo-devel@o2.pl>             *
# *   Code has been adopted to Crowdin API v2 and extended                  *
# *                                                                         *
# ***************************************************************************

"""
This script allows you to manage the translations
of your workbench with crowdin.

USAGE:

updateTranslations [command]

Possible commands are:

* updatets: Updates the ts files found in your WB
* upload: Sends the ts file to crowdin
* build-status: Shows current build status
* build: Creates a ready-for-download zip file on crowdin
* download: Download the zip file created in previous step
* install: Unzips the above file and creates corresponding qm files
* status: Shows translation status of main workbench ts file
  (filename: MODULENAME.ts)

Prior to using this script, you must have been made an manager on crowdin
freecad-addons project (ask Yorik), and you must have added your APIv2 token
in a simple text file named ~/.crowdin-freecadaddons
You must also adapt the config values below. There is nothing else to do if
your workbench includes only .py and .ui files. They will all be gathered
automatically under one single ts file by this script.

"""

from __future__ import print_function

import sys
import os
import tempfile
import shutil
import zipfile
from pathlib import Path
import concurrent.futures
import json
from collections import namedtuple
from functools import lru_cache
from urllib.parse import quote_plus
from urllib.request import Request
from urllib.request import urlopen
from urllib.request import urlretrieve
from urllib.error import HTTPError


### CONFIGURATION

# adapt the following values to your workbench

# the name of your workench, and also the .ts file. Ex: "BIM" means the ts file is BIM.ts
MODULENAME = "Cables"

# The base path of your module, relative to this file
BASEPATH = "../.."

# the path to the translations files location, inside your module folder
TRANSLATIONSPATH = "resources/translations"

# the list of languages to install
# LANGUAGES = None to use all found in the zip file
LANGUAGES = "af ar ca cs de el es-ES eu fi fil fr gl hr hu id it ja kab ko lt nl no pl pt-BR pt-PT ro ru sk sl sr sv-SE tr uk val-ES vi zh-CN zh-TW"

# List of supported languages FreeCADGui.supportedLocales().values()
LANG = ['en', 'af', 'ar', 'eu', 'be', 'bg', 'ca', 'zh-CN', 'zh-TW', 'hr', 'cs', 'da', 'nl', 'fil', 'fi', 'fr', 'gl', 'ka', 'de', 'el', 'hu', 'id', 'it', 'ja', 'kab', 'ko', 'lt', 'no', 'pl', 'pt-PT', 'pt-BR', 'ro', 'ru', 'sr', 'sr-CS', 'sk', 'sl', 'es-ES', 'es-AR', 'sv-SE', 'tr', 'uk', 'val-ES', 'vi']


# pylupdate util to use (pylupdae5, pyside2-lupdate,...)
# #PYLUPDATE = "pyside2-lupdate -verbose"
PYLUPDATE = "lupdate"

# lrelease util to use
PYLRELEASE = "lrelease"

# Treshold used to filter out untranslated languages, used in status command
THRESHOLD = 0.1

# Token file name
TOKENFILE = ".crowdin-freecadaddons"

# Project name in Crowdin. Do not change it.
PROJECT_IDENTIFIER = "freecad-addons"

### END CONFIGURATION

TsFile = namedtuple("TsFile", ["filename", "src_path"])


class CrowdinUpdater:
    '''
    Class copied from https://github.com/FreeCAD/FreeCAD/blob/main/src/Tools/updatecrowdin.py
    and modified to better fit external workbench translation
    '''
    BASE_URL = "https://api.crowdin.com/api/v2"

    def __init__(self, project_identifier, workbench_filename=None, multithread=False):
        self.project_identifier = project_identifier
        self.wbfilename = workbench_filename
        self.multithread = multithread

    @lru_cache()
    def _get_project_id(self):
        url = f"{self.BASE_URL}/projects"
        response = self._make_api_req(url)

        for project in [p["data"] for p in response]:
            if project["identifier"] == self.project_identifier:
                return project["id"]

        raise Exception("No project identifier found!")

    @lru_cache()
    def _get_wbfile_id(self):
        files_info = self._get_files_info()
        if self.wbfilename in files_info:
            return files_info[self.wbfilename]

        raise Exception("No workbench file identifier found!")

    def _make_file_api_req(self, file_path, *args, **kwargs):
        pid = self._get_project_id()
        fid = self._get_wbfile_id()
        url = f"{self.BASE_URL}/projects/{pid}/files/{fid}{file_path}"
        return self._make_api_req(url=url, *args, **kwargs)

    def _make_project_api_req(self, project_path, *args, **kwargs):
        url = f"{self.BASE_URL}/projects/{self._get_project_id()}{project_path}"
        return self._make_api_req(url=url, *args, **kwargs)

    def _make_api_req(self, url, extra_headers={}, method="GET", data=None):
        headers = {"Authorization": "Bearer " + load_token(), **extra_headers}

        if type(data) is dict:
            headers["Content-Type"] = "application/json"
            data = json.dumps(data).encode("utf-8")

        request = Request(url, headers=headers, method=method, data=data)
        return json.loads(urlopen(request).read())["data"]

    def _get_files_info(self):
        files = self._make_project_api_req("/files?limit=250")
        return {f["data"]["path"].strip("/"): str(f["data"]["id"]) for f in files}

    def _add_storage(self, filename, fp):
        response = self._make_api_req(
            f"{self.BASE_URL}/storages",
            data=fp,
            method="POST",
            extra_headers={
                "Crowdin-API-FileName": filename,
                "Content-Type": "application/octet-stream",
            },
        )
        return response["id"]

    def _update_file(self, project_id, ts_file, files_info):
        filename = quote_plus(ts_file.filename)

        with open(ts_file.src_path, "rb") as fp:
            storage_id = self._add_storage(filename, fp)

        if filename in files_info:
            file_id = files_info[filename]
            res = self._make_project_api_req(
                f"/files/{file_id}",
                method="PUT",
                data={
                    "storageId": storage_id,
                    "updateOption": "keep_translations_and_approvals",
                },
            )
            print(f"  id:{res['id']}, name:{res['name']}, revision:{res['revisionId']}, updated:{res['updatedAt']}")
            print(f"{filename} updated")
        else:
            res = self._make_project_api_req("/files", data={"storageId": storage_id, "name": filename})
            print(f"  id:{res['id']}, name:{res['name']}, revision:{res['revisionId']}, updated:{res['updatedAt']}")
            print(f"{filename} uploaded")

    def status(self):
        response = self._make_project_api_req("/languages/progress?limit=100")
        return [item["data"] for item in response]

    def status_wb(self):
        response = self._make_file_api_req("/languages/progress?limit=100")
        return[item["data"] for item in response]

    def download(self, build_id):
        filename = f"{self.project_identifier}.zip"
        response = self._make_project_api_req(f"/translations/builds/{build_id}/download")
        urlretrieve(response["url"], filename)
        print("Download finished.")

    def build(self):
        return self._make_project_api_req("/translations/builds", data={}, method="POST")

    def build_status(self):
        response = self._make_project_api_req("/translations/builds")
        return [item["data"] for item in response]

    def update(self, ts_files):
        files_info = self._get_files_info()
        futures = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            for ts_file in ts_files:
                if self.multithread:
                    future = executor.submit(
                        self._update_file, self.project_identifier, ts_file, files_info
                    )
                    futures.append(future)
                else:
                    self._update_file(self.project_identifier, ts_file, files_info)

        # This blocks until all futures are complete and will also throw any exception
        for future in futures:
            print(f"{future.result()} done.")
            future.result()


def load_token():
    # try to read token from ~/TOKENFILE
    config_file = os.path.join(os.path.expanduser("~"), TOKENFILE)
    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            token = file.read().strip()
            if token:
                return token
    # if file does'nt exists read from CROWDIN_TOKEN
    return os.environ.get("CROWDIN_TOKEN")


def doLanguage(tempfolder, translationsfolder, lncode):
    "copies and compiles a single ts file"

    if lncode == "en":
        # never treat "english" translation... For now :)
        return
    p = Path(tempfolder)
    ts_list = list(p.glob('*.ts'))
    tsfilepath = None
    for f in ts_list:
        if lncode in f.stem.split('_')[1]:
            tsfilepath = f.as_posix()
            break
    if not tsfilepath:
        return
    newtspath = os.path.join(translationsfolder, MODULENAME + "_" + lncode + ".ts")
    newqmpath = os.path.join(translationsfolder, MODULENAME + "_" + lncode + ".qm")
    # print(tsfilepath)
    # print(newtspath)
    empty, total = count_translations(tsfilepath)
    if (total-empty)/total < THRESHOLD:
        print(f"  {lncode} has only {100.0*(total-empty)/total:.1f}% of translation. Dropping...")
        return
    shutil.copyfile(tsfilepath, newtspath)
    os.system(f"{PYLRELEASE} " + newtspath)
    if not os.path.exists(newqmpath):
        print("ERROR: unable to create", newqmpath, ", aborting")
        sys.exit()
    if os.stat(newqmpath).st_size < 100:
        print(f"{newqmpath} not translated, deleting...")
        os.remove(newtspath)
        os.remove(newqmpath)


def count_translations(filename):
    pattern_no = 'translation type="unfinished"'
    pattern_yes = '<translation>'
    counter_no = 0
    counter_yes = 0
    with open(filename, 'r') as fp:
        for line in fp:
            if pattern_no in line:
                counter_no += 1
            if pattern_yes in line:
                counter_yes += 1
    return counter_no, counter_no + counter_yes


if __name__ == "__main__":
    "main thread"

    # only one argument allowed
    arg = sys.argv[1:]
    if len(arg) != 1:
        print(__doc__)
        sys.exit()
    arg = arg[0]

    # checking API key stored in ~/TOKENFILE
    if arg not in ["install", "updatets", "help"]:
        if load_token() is None:
            print("Config file and token not found!")
            sys.exit()
        updater = CrowdinUpdater(PROJECT_IDENTIFIER, MODULENAME + ".ts")
        try:
            updater.status()
            print("Token ok")
        except HTTPError as err:
            print(f"Token access failed: {err}")
    else:
        updater = None

    basepath = os.path.abspath(BASEPATH)
    transpath = os.path.join(basepath, TRANSLATIONSPATH)

    if arg == "updatets":
        os.chdir(basepath)
        # os.system("lupdate *.ui -ts "+os.path.join(transpath,"uifiles.ts"))
        # os.system(PYLUPDATE+" *.py -ts "+os.path.join(transpath,"pyfiles.ts"))
        # os.system("lconvert -i "+os.path.join(transpath,"uifiles.ts")+" "+os.path.join(transpath,"pyfiles.ts")+" -o "+os.path.join(transpath,MODULENAME+".ts"))
        # os.system("rm "+os.path.join(transpath,"uifiles.ts"))
        # os.system("rm "+os.path.join(transpath,"pyfiles.ts"))
        cmd = (
            PYLUPDATE
            + ' `find ./ -name "*.py"` `find ./ -name "*.ui"` -ts '
            + os.path.join(transpath, MODULENAME + ".ts")
        )
        os.system(cmd)
        print("Updated", os.path.join(transpath, MODULENAME + ".ts"))

    elif arg == "build":
        print(
            "Building (warning, this can be invoked only once per 30 minutes)... ",
            end="",
        )
        data = updater.build()
        print(f"  id: {data['id']}, progress: {data['progress']}%, status: {data['status']}, created at: {data['createdAt']}")

    elif arg == "build-status":
        print("Build status:")
        data = updater.build_status()
        for item in data:
            print(f"  id: {item['id']}, progress: {item['progress']}%, status: {item['status']}, created at: {item['createdAt']}")

    elif arg == "download":
        stat = updater.build_status()
        if not stat:
            print("No builds found. Download failed!")
        else:
            print("Available builds:")
            for item in stat:
                print(f"  id: {item['id']}, progress: {item['progress']}%, status: {item['status']}, created at: {item['createdAt']}")
            print(f"Downloading from build id = {stat[0]['id']} ...")
            updater.download(stat[0]["id"])
            print(f"Downloaded {PROJECT_IDENTIFIER}.zip into current directory.")

    elif arg == "upload":
        print("Sending " + MODULENAME + ".ts... ")
        fname = f"{MODULENAME}.ts"
        ts_files = [TsFile(fname, os.path.join(transpath, fname))]
        updater.update(ts_files)
        print("Done.")

    elif arg == "status":
        items = updater.status_wb()
        total = items[0]['phrases']['total']
        print(f"\nServer side: total number of phrases = {total}\n")
        print(f"Translations with more then {THRESHOLD*100:.0f}% of work done:")
        for i in items:
            empty = i['phrases']['total'] - i['phrases']['translated']
            progress = i['translationProgress']
            if progress > THRESHOLD*100.0:
                print(f"{i['languageId']: >5}: {progress:>6.2f}%, {empty:4d}/{total} untranslated phrases")
        _, total = count_translations(f"{MODULENAME}.ts")
        print(f"\n\nLocal side: total number of phrases = {total}\n")
        filelist = [f for f in Path(transpath).glob(f"{MODULENAME}_*.ts")]
        filelist.sort()
        for fpath in filelist:
            empt, tot = count_translations(fpath)
            lang = fpath.stem.split("_")[1]
            print(f"{lang: >5}: {100.0*(tot-empt)/total:>6.2f}%, {empt:4d}/{tot} untranslated phrases")
        print()

    elif arg == "install":
        zippath = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), f"{PROJECT_IDENTIFIER}.zip"
        )
        tempfolder = tempfile.mkdtemp()
        print("creating temp folder " + tempfolder)
        os.chdir(tempfolder)
        if not os.path.exists(zippath):
            print("ERROR: " + zippath + " not found")
            sys.exit()
        shutil.copy(zippath, tempfolder)
        zfile = zipfile.ZipFile(os.path.join(tempfolder, os.path.basename(zippath)))
        print("extracting zip...")
        zfile.extractall()
        os.chdir(transpath)
        # if not LANGUAGES:
        #    LANGUAGES = " ".join([n[:-1] for n in zfile.namelist() if n.endswith("/")])
        for ln in LANG:
            tpath = os.path.join(tempfolder, MODULENAME)
            if not os.path.exists(tpath):
                print("ERROR: language path", path, "not found!")
            else:
                doLanguage(tpath, transpath, ln)

    else:
        print(__doc__)
