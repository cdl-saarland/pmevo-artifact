#!/usr/bin/env python3
# vim: et:ts=4:sw=4:fenc=utf-8

import datetime
import os
import shutil
import textwrap
from collections import defaultdict

# This script generates html code from a json list containing entries of the
# following form:
#
# entry = {
#     "category": category,
#     "caption": caption,
#     "creation_date": date,
#     "content":[
#             {
#                 "kind": "image",
#                 "path": path
#             },
#             {
#                 "kind": "table",
#                 "rows": [["MAPE", "X%"],
#                          ["Pearson CC", "Y"],
#                          ["Spearman CC", "Z"]]
#             },
#             {
#                 "kind": "text",
#                 "text": text
#             }
#        ]
# }
#

def to_html(entry, image_paths=[]):
    outstr = ""
    outstr += "<div class='entry'>\n"
    caption = entry["caption"]
    if caption is not None:
        outstr += "    <h2>\n"
        outstr += "         " + caption + ":\n"
        outstr += "    </h2>\n"
    outstr += "    <div class='content'>\n"
    for obj in entry["content"]:
        if obj["kind"] == "image":
            image_paths.append(obj["path"])
            img_name = "img/" + os.path.basename(obj["path"])
            outstr += "        <div class='imagewrapper'>\n"
            outstr += "            <img class='image' src='{}' alt='Here, an image is missing!'>\n".format(img_name)
            outstr += "        </div>\n"
        elif obj["kind"] == "table":
            outstr += "        <table>\n"
            for row in obj["rows"]:
                outstr += "            <tr>\n"
                for col in row:
                    outstr += "                <td>{}</td>\n".format(col)
            outstr += "        </table>\n"
        elif obj["kind"] == "text":
            outstr += "        <p>{}</p>\n".format(obj["text"])
        else:
            assert False, "Unknown content kind!"

    outstr += "    </div>\n"
    outstr += "</div>\n"
    return outstr


def main():
    default_path = "/var/www/html/"
    import argparse
    import json
    argparser = argparse.ArgumentParser(description='Generate a static result website from data')
    argparser.add_argument('infiles', nargs='*', help='input result json')
    argparser.add_argument('-o', '--outpath', default=default_path, help='destination directory (default: {})'.format(default_path))
    argparser.add_argument('--dryrun', action='store_true', help='only print the resulting html file')
    args = argparser.parse_args()

    frame_path = os.path.join(os.path.dirname(__file__), "frame.html")
    frame_begin = ""
    frame_end = ""
    with open(frame_path, 'r') as frame_file:
        in_begin = True
        for line in frame_file.readlines():
            if "INSERT CONTENT HERE" in line:
                in_begin = False
            else:
                if in_begin:
                    frame_begin += line
                else:
                    frame_end += line

    content = ""

    image_paths = []

    categories = defaultdict(list)

    for inpath in args.infiles:
        with open(inpath, "r") as infile:
            data = json.load(infile)
            for entry in data:
                category = entry["category"]
                if category is None:
                    category = "default"
                date_str = entry.get("creation_date", None)
                if date_str is None:
                    date = datetime.datetime.now()
                else:
                    date = datetime.datetime.strptime(date_str,"%Y-%m-%dT%H:%M:%S.%f")
                categories[category].append( (date, to_html(entry, image_paths)) )

    for cat, ds in categories.items():
        ds.sort(key=lambda x: x[0], reverse=True)

    for date, data in categories["default"]:
        content += data

    for cat, ds in categories.items():
        if cat == "default":
            continue
        content += "<h1>{}</h1>\n".format(cat)
        for date, data in ds:
            content += data

    if len(content) == 0:
        content = to_html({ "category": None, "caption": None, "content": [{"kind": "text", "text": "This page will contain evaluation results once generated."}]})

    content = textwrap.indent(content, "        ")

    res_html = frame_begin + content + frame_end

    if args.dryrun:
        print(res_html)
    else:
        # make img directory
        dest_image_path = os.path.join(args.outpath, "img")
        try:
            os.makedirs(dest_image_path)
        except FileExistsError:
            pass

        with open(os.path.join(args.outpath, "index.html"), "w") as outfile:
            outfile.write(res_html)

        # copy relevant images to img directory
        for p in image_paths:
            shutil.copy(p, dest_image_path)


if __name__ == "__main__":
    main()
