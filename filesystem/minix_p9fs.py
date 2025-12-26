"""A plan9 file server for operating on an image of the Minix file system.

The implementation for pyroute2 looks better however that package is heavily
non-Windows, so uses https://github.com/pbchekin/p9fs-py/blob/main/src/py9p
maintained by pbchekin.

TODO:
- Write support - required write support in the minix module first.
- Extend the logging to include include where the requests came from,.which is
  req.sock.sock.raddr
"""

# /// script
# dependencies = [
#   "p9fs",
# ]
# ///

import logging
import os
import pathlib
import posixpath
import stat as stat_module

import minix
from p9fs import py9p


LOGGER = logging.getLogger(
    "minix_p9fs" if __name__ == "__main__" else __name__,
)


class MinixFs:
    def __init__(self, image_path: pathlib.Path):
        self.reader = image_path.open("rb")
        self.system = minix.LoadedSystem.from_reader(self.reader)
        self.root = self.pathtodir("/")
        self.root.localpath = pathlib.PurePosixPath("/")
        self.files = {
            self.root.qid.path: self.root,
        }

    def close(self):
        self.system = None
        self.reader.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # Expected interface
    def getfile(self, path):
        return self.files.get(path, None)

    def pathtodir(self, path) -> py9p.Dir:
        LOGGER.info(f"pathtodir [%s]", path)
        stat = self.system.stat(path)
        return self.stat_to_dir(path, stat)

    def stat_to_dir(self, path: os.PathLike | str, stat: os.stat_result) -> py9p.Dir:
        """Convert a stat_result to the plan 9 dir type."""
        if stat.st_uid == 0:
            user = "root"
        else:
            raise ValueError("Non-root user NYI")

        if stat.st_gid == 0:
            group = "root"
        else:
            raise ValueError("Non-root user NYI")

        file_type = 0
        res = stat.st_mode & 0o777
        if stat_module.S_ISDIR(stat.st_mode):
            res |= py9p.DMDIR
            file_type |= py9p.QTDIR

        device = 999
        qid = py9p.Qid(file_type, 0, py9p.hash8(os.fspath(path)))
        return py9p.Dir(
            0,
            0,
            device,
            qid,
            res,
            int(stat.st_atime),
            int(stat.st_mtime),
            stat.st_size,
            os.path.basename(path),
            user,
            group,
            user,
        )

    def open(self, srv, req):
        f = self.getfile(req.fid.qid.path)
        if not f:
            srv.respond(req, "unknown file")
            return

        LOGGER.info(f"open [%s]", f.localpath)
        stat = self.system.stat(f.localpath)
        if (req.ifcall.mode & 3) == py9p.OWRITE:
            srv.respond(req, "read-only file server")
            return
        elif (req.ifcall.mode & 3) == py9p.ORDWR:
            srv.respond(req, "read-only file server")
        else:  # py9p.OREAD and otherwise
            m = "rb"

        if not (f.qid.type & py9p.QTDIR) and not stat_module.S_ISLNK(stat.st_mode):
            f.fd = self.system.open(f.localpath, m)

        srv.respond(req, None)

    def walk(self, srv, req):
        f = self.getfile(req.fid.qid.path)
        if not f:
            srv.respond(req, "unknown file")
            return

        npath = f.localpath
        for path in req.ifcall.wname:
            # The normpath() handles collapsing .. and . as the pure paths
            # lack the resolve() function for doing the same thing.
            npath = pathlib.PurePosixPath(posixpath.normpath(npath / path))

            if path == "." or path == "":
                req.ofcall.wqid.append(f.qid)
            elif path == "..":
                # .. resolves to the parent, cycles at /
                qid = f.parent.qid
                req.ofcall.wqid.append(qid)
                f = f.parent
            else:
                try:
                    d = self.pathtodir(npath)
                except:
                    LOGGER.warning("File not found: %s", npath)
                    srv.respond(req, "file not found")
                    return

                nf = self.getfile(d.qid.path)
                if nf:
                    # already exists, just append to req
                    req.ofcall.wqid.append(d.qid)
                    f = nf
                else:
                    d.localpath = npath
                    d.basedir = d.localpath.parent
                    # "/".join(npath.split("/")[:-1])
                    d.parent = f
                    self.files[d.qid.path] = d
                    req.ofcall.wqid.append(d.qid)
                    f = d

        req.ofcall.nwqid = len(req.ofcall.wqid)
        srv.respond(req, None)

    def remove(self, srv, req):
        LOGGER.info("remove")

    def create(self, srv, req):
        LOGGER.info("create")

    # def clunk(self, srv, req):
    #     LOGGER.info("clunk")

    def stat(self, srv, req):
        """Respond to the Tstat message."""
        f = self.getfile(req.fid.qid.path)
        if not f:
            srv.respond(req, "unknown file")
            return
        req.ofcall.stat.append(self.pathtodir(f.localpath))
        srv.respond(req, None)

    def wstat(self, srv, req):
        LOGGER.info("wstat")

    def read(self, srv, req):
        f = self.getfile(req.fid.qid.path)
        if not f:
            srv.respond(req, "unknown file")
            return

        inode = self.system._path_to_inode(f.localpath)
        if f.qid.type & py9p.QTDIR:
            LOGGER.info("read directory: %s", f.localpath)
            directory = self.system.read_directory(inode)

            # no need to add anything to self.files yet
            # wait until they walk to it
            l = filter(
                lambda entry: entry.filename not in (b".", b".."), directory.entries
            )
            # The performance of this could be improved to skip the path
            # look-up and use the inodes, or have a stat_to_dir().
            # path / child.filename.decode("utf-8"),
            req.ofcall.stat = [
                self.pathtodir(f.localpath / entry.filename.decode("utf-8"))
                for entry in l
            ]
        else:
            LOGGER.info("read file: %s", f.localpath)
            f.fd.seek(req.ifcall.offset)
            req.ofcall.data = f.fd.read(req.ifcall.count)
        srv.respond(req, None)

    def write(self, srv, req):
        LOGGER.info("write")


if __name__ == "__main__":
    srv = py9p.Server(listen=("0.0.0.0", 8999), chatty=False)
    if not srv.chatty:
        logging.basicConfig(level=logging.INFO)
    assert not srv.dotu, "NYI"
    with MinixFs(pathlib.Path.cwd() / "minixfs.raw") as fs:
        srv.mount(fs)
        if not srv.chatty:
            print(f"Listening {srv.host} on port {srv.port}")
        srv.serve()
