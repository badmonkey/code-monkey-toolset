def write_json(self, doc_uid: TUUID, data: TJson) -> None:
    filepath = self._make_filepath(doc_uid, create=True)

    if os.path.isfile(filepath):
        tmpfilepath = filepath + ".write-tmp"
        with open(tmpfilepath, "w") as f:
            f.write(json.dumps(data))
            f.close()
        os.rename(tmpfilepath, filepath)
    else:
        with open(filepath, "w") as f:
            f.write(json.dumps(data))
            f.close()
