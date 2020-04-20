# vim: et:ts=4:sw=4:fenc=utf-8

from abc import ABC, abstractmethod
import datetime
import json
import os
import sys

try:
    import git
    git_available = True
except ImportError:
    git_available = False

def filename_append(fn, suffix):
    if fn.endswith(".json"):
        fn = fn[:-len(".json")]
    fn += suffix
    fn += ".json"
    return fn

class Vault:
    """ A persistent progress storage for lists of json data.
    """
    def __init__(self, outfile=None, progressfile=None, debug=False):
        self.debug = debug
        self.default_progress_id = 0
        assert(outfile is not None or progressfile is not None)
        if outfile is not None:
            self.outfilename = outfile
            if progressfile is not None:
                self.progressfile = progressfile
            else:
                self.progressfile = self.outfilename + ".progress"
        else:
            self.progressfile = progressfile
            if progressfile.endswith(".json.progress"):
                self.outfilename = progressfile[:-len(".progress")]
            else:
                self.outfilename = progressfile + ".final.json"

        self.model = []
        self.to_write = []

        if os.path.isfile(self.progressfile):
            if self.debug:
                print("Found progressfile with the name '{}'!".format(self.progressfile), file=sys.stderr)
            try:
                self.load_progress()
            except json.decoder.JSONDecodeError as e:
                print("Vault Error: Failed to load progress from '{}'!\n  Fix or remove the file to continue.".format(self.progressfile), file = sys.stderr)
                sys.exit(73)
        else:
            if self.debug:
                print("No progressfile found with the name '{}'!".format(self.progressfile), file=sys.stderr)
            with open(self.progressfile, "w") as progressfile:
                progressfile.write("[\n")

        self.first_entry = (self.last_progress() is None)

    def last_progress(self):
        if len(self.model) == 0:
            return None

        return self.model[-1][0]

    def load_progress(self):
        if not os.path.isfile(self.progressfile):
            return

        with open(self.progressfile, "r") as infile:
            datastr = infile.read()
            datastr += "\n]\n"
            datalist = json.loads(datastr)

        assert(isinstance(datalist, list))
        self.model = datalist

    def add(self, new_data, progress_id=None, do_save=True):
        if progress_id is None:
            progress_id = self.default_progress_id
            self.default_progress_id += 1
        new_entry = (progress_id, new_data)
        self.model.append(new_entry)
        self.to_write.append(new_entry)
        if do_save:
            self.save_progress()

    def save_progress(self):
        if len(self.to_write) == 0:
            return

        with open(self.progressfile, "a") as progressfile:
            for progress_id, new_data in self.to_write:
                if self.first_entry:
                    progressfile.write("\n")
                    self.first_entry = False
                else:
                    progressfile.write(",\n")
                print(obj_to_json_str([progress_id, new_data], dump_noindent=True), file=progressfile, end='')

        self.to_write.clear()

    def finalize(self, delete_progress=True):
        jsondata = [ data for progress_id, data in self.model]
        with open(self.outfilename, "w") as outfile:
            outfile.write(obj_to_json_str(jsondata))
            outfile.write("\n")

        if delete_progress and os.path.isfile(self.progressfile):
            os.remove(self.progressfile)

def mark_noindent(obj):
    return ["__noindent__", obj]

def is_noindent(obj):
    return isinstance(obj, list) and len(obj) == 2 and obj[0] == "__noindent__"

def unwrap_noindent(obj):
    assert(is_noindent(obj))
    return obj[1]


indent_str = "  "

def obj_to_json_str(obj, indent=0, dump_noindent=False):
    if is_noindent(obj):
        if dump_noindent:
            return json.dumps(obj)
        else:
            return json.dumps(unwrap_noindent(obj))
    elif isinstance(obj, dict):
        res = "{\n" + (indent + 1) * indent_str
        first = True
        for k, v in obj.items():
            if not first:
                res += ",\n" + (indent + 1) * indent_str
            first = False
            res += obj_to_json_str(k, indent + 1, dump_noindent=dump_noindent)
            res += ": "
            res += obj_to_json_str(v, indent + 1, dump_noindent=dump_noindent)
        res += "\n" + indent * indent_str + "}"
        return res
    elif isinstance(obj, list):
        res = "[\n" + (indent + 1) * indent_str
        first = True
        for v in obj:
            if not first:
                res += ",\n" + (indent + 1) * indent_str
            first = False
            res += obj_to_json_str(v, indent + 1, dump_noindent=dump_noindent)
        res += "\n" + indent * indent_str + "]"
        return res
    elif isinstance(obj, JSONable):
        return obj_to_json_str(obj.to_json_dict())
    elif isinstance(obj, int):
        return '"{}"'.format(obj)
    else:
        return json.dumps(obj)

class JSONable(ABC):
    # TODO get_kind(self)
    def __init__(self):
        self.metadata = None

    def add_metadata(self):
        if self.metadata is not None:
            return
        # add some interesting metadata
        res = dict()
        res["creation_date"] = datetime.datetime.now().isoformat()
        if git_available:
            repo = git.Repo(search_parent_directories=True)
            label = repo.head.object.hexsha
        else:
            label = "unknown, install gitpython!"
        res["pmtestbench_version"] = label
        self.metadata = res

    @abstractmethod
    def from_json_dict(self, jsondict):
        pass

    @abstractmethod
    def to_json_dict(self):
        pass

    def to_json_str(self, jsondict):
        if self.metadata is not None:
            annotated_dict = { k: v for k, v in jsondict.items() }
            assert "metadata" not in annotated_dict
            annotated_dict["metadata"] = self.metadata
            return obj_to_json_str(annotated_dict)
        else:
            return obj_to_json_str(jsondict)

    def __str__(self):
        jsondict = self.to_json_dict()
        return self.to_json_str(jsondict)
        # return json.dumps(jsondict, indent=2, separators=(",", ": "))

    @classmethod
    def from_json(cls, infile, *args, **kwargs):
        jsondict = json.load(infile)
        res = cls(*args, **kwargs)
        res.from_json_dict(jsondict)
        return res

    @classmethod
    def from_json_str(cls, instring, *args, **kwargs):
        jsondict = json.loads(instring)
        res = cls(*args, **kwargs)
        res.from_json_dict(jsondict)
        return res

    def to_json(self, outfile):
        self.add_metadata()
        jsondict = self.to_json_dict()
        outfile.write(self.to_json_str(jsondict))
        # json.dump(jsondict, outfile, indent=2, separators=(",", ": "))


