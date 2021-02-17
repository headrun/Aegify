import os, time, sys

SOURCE = "clinicalinvestigators"

def delete_older_files(path):
    now = time.time()
    for f in os.listdir(path):
        f = os.path.join(path, f)
        if os.stat(f).st_mtime < now - 15 * 86400:
            if os.path.isfile(f):
                os.remove(os.path.join(path, f))
