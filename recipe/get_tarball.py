#!/usr/bin/env python
from __future__ import print_function
import argparse
from glob import glob
import hashlib
import os
import io
from six.moves.urllib.request import urlretrieve
import shutil
import tarfile
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('url')
parser.add_argument('--checksum', '-c', required=True)
parser.add_argument('--checksum-type', '-t', default='sha256')
parser.add_argument('--out-path', '-p', default='.')
parser.add_argument('--strip-components', type=int, default=0)
args = parser.parse_args()

# should be possible to do this in one pass, but requires "tee"ing the file to
# both GzipFile and hashlib, so whatever.

tar_fn, _ = urlretrieve(args.url)

try:
    digest = hashlib.new(args.checksum_type)
    chunksize = 32 * 2**20
    with io.open(tar_fn, 'rb') as f:
        while True:
            x = f.read(chunksize)
            digest.update(x)
            if not x:
                break
    d = digest.hexdigest()
    if d != args.checksum:
        parser.error("Bad digest: expected {}, got {}".format(args.checksum, d))

    if not os.path.exists(args.out_path):
        os.makedirs(args.out_path)

    with tarfile.open(tar_fn, 'r') as tar:
        if not args.strip_components:
            tar.extractall(args.out_path)
        else:
            # hacky way to do this...
            tmpdir = tempfile.mkdtemp(dir=os.path.dirname(args.out_path))
            try:
                tar.extractall(tmpdir)
                print('extracted to {}'.format(tmpdir))

                tup = ('*',) * (args.strip_components + 1)
                for fn in glob(os.path.join(tmpdir, *tup)):
                    target = os.path.join(args.out_path, os.path.basename(fn))
                    os.rename(fn, target)
            finally:
                shutil.rmtree(tmpdir)
finally:
    os.remove(tar_fn)
