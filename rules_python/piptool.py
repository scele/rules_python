# Copyright 2017 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The piptool module imports pip requirements into Bazel rules."""

import argparse
import ast
import atexit
import collections
import hashlib
import io
import itertools
import json
import os
import pkgutil
import pkg_resources
import re
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import shutil
import sys
import tempfile
import toposort
import zipfile
from six.moves import urllib

# Note: We carefully import the following modules in a particular
# order, since these modules modify the import path and machinery.
import pkg_resources


def extract_packages(package_names):
    """Extract zipfile contents to disk and add to import path"""

    # Set a safe extraction dir
    extraction_tmpdir = tempfile.mkdtemp()
    atexit.register(lambda: shutil.rmtree(
        extraction_tmpdir, ignore_errors=True))
    pkg_resources.set_extraction_path(extraction_tmpdir)

    # Extract each package to disk
    dirs_to_add = []
    for package_name in package_names:
        req = pkg_resources.Requirement.parse(package_name)
        extraction_dir = pkg_resources.resource_filename(req, '')
        dirs_to_add.append(extraction_dir)

    # Add extracted directories to import path ahead of their zip file
    # counterparts.
    sys.path[0:0] = dirs_to_add
    existing_pythonpath = os.environ.get('PYTHONPATH')
    if existing_pythonpath:
        dirs_to_add.extend(existing_pythonpath.split(':'))
    os.environ['PYTHONPATH'] = ':'.join(dirs_to_add)


# Wheel, pip, and setuptools are much happier running from actual
# files on disk, rather than entries in a zipfile.  Extract zipfile
# contents, add those contents to the path, then import them.
extract_packages(['pip', 'setuptools', 'wheel'])

# Defeat pip's attempt to mangle sys.path
saved_sys_path = sys.path
sys.path = sys.path[:]
import pip
import pip._internal
sys.path = saved_sys_path

import setuptools
import wheel


def pip_main(argv, env=None):
    # Extract the certificates from the PAR following the example of get-pip.py
    # https://github.com/pypa/get-pip/blob/04e994a41ff0a97812d6d2/templates/default.py#L167-L171
    cert_path = os.path.join(tempfile.mkdtemp(), "cacert.pem")
    with open(cert_path, "wb") as cert:
      cert.write(pkgutil.get_data("pip._vendor.certifi", "cacert.pem"))
    argv = ["--disable-pip-version-check", "--cert", cert_path] + argv
    old_env = os.environ.copy()
    try:
      if env:
        os.environ.update(env)
      return pip._internal.main(argv)
    finally:
      os.environ.clear()
      os.environ.update(old_env)

from rules_python.whl import Wheel


global_parser = argparse.ArgumentParser(
    description='Import Python dependencies into Bazel.')
subparsers = global_parser.add_subparsers()

def split_extra(s):
  parts = s.split("[")
  if len(parts) == 1:
    return parts[0], None
  return parts[0], parts[1][:-1]

class CaptureOutput():
  def write(self, data):
    self.stdout_save.write(data)
    self.stdout.write(data.encode())
  def __getattr__(self, name):
    return getattr(self.stdout_save, name)
  def __enter__(self):
    self.stdout_save = sys.stdout
    self.stdout = io.BytesIO()
    sys.stdout = self
    return self
  def __exit__(self, *exc_details):
    sys.stdout = self.stdout_save


# piptool build
# -------------

def build_wheel(distribution,
                version,
                directory,
                cache_key=None,
                build_dir=None,
                build_env=None,
                build_deps=None,
                sha256=None,
                pip_args=None,
                resolving=False):
  env = {}

  home = None
  if build_dir:
    home = build_dir.rstrip("/") + ".home"
    if os.path.isdir(home):
      shutil.rmtree(home)
    os.makedirs(home)
  else:
    home = tempfile.mkdtemp()

  cmd = ["wheel"]
  cmd += ["-w", directory]

  # Allowing "pip wheel" to download setup_requires packages with easy_install would
  # poke a hole to our wheel version locking scheme, making wheel builds non-deterministic.
  # Disable easy_install as instructed here:
  #   https://pip.pypa.io/en/stable/reference/pip_install/#controlling-setup-requires
  # We set HOME to the current directory so pip will look at this file; see:
  #   https://docs.python.org/2/install/index.html#distutils-configuration-files
  env["HOME"] = home
  with open(os.path.join(home, ".pydistutils.cfg"), "w") as f:
    f.write("[easy_install]\nallow_hosts = ''\n")

  for d in build_deps or []:
    Wheel(d).expand(home)

  # Process .pth files of the extracted build deps.
  with open(os.path.join(home, "sitecustomize.py"), "w") as f:
    f.write("import site; import os; site.addsitedir(os.path.dirname(__file__))")

  # Set PYTHONPATH so that all extracted buildtime dependencies are available.
  env["PYTHONPATH"] = ":".join(os.environ.get("PYTHONPATH", "").split(":") + [home])
  env["CFLAGS"] = " ".join([
      "-D__DATE__=\"redacted\"",
      "-D__TIMESTAMP__=\"redacted\"",
      "-D__TIME__=\"redacted\"",
      "-Wno-builtin-macro-redefine",
  ])

  # We don't want .pyc files end up in the built wheels!
  env["PYTHONDONTWRITEBYTECODE"] = "1"

  # Set any other custom env variables the user wants to add to the wheel build.
  env.update(dict([x.split("=", 1) for x in build_env or []]))

  # For determinism, canonicalize distribution name to lowercase here, since, lo and
  # behold, the wheel contents may be different depending on the case passed to
  # "pip wheel" command...
  cmd += ["%s==%s" % (distribution.lower(), version)]

  cmd += ["--no-cache-dir"]
  cmd += ["--no-deps"]

  # Build the wheel in a deterministic path so that any debug symbols have stable
  # paths and the resulting wheel has a higher chance of being deterministic.
  if build_dir:
    if os.path.isdir(build_dir):
      shutil.rmtree(build_dir)
    cmd += ["--build", build_dir]

  cmd += pip_args or []

  locally_built = False
  with CaptureOutput() as output:
    if pip_main(cmd, env):
      print("pip command failed: " + str(cmd))
      sys.exit(1)
    if re.search(r"Running setup\.py bdist_wheel", output.stdout.getvalue().decode()):
      locally_built = True

  wheels = wheels_from_dir(directory)
  assert len(wheels) == 1
  wheel = wheels[0]

  if locally_built:
    # The wheel was built locally. For determinism, we need to strip timestamps
    # from the zip-file.
    strip_wheel(wheel)

  computed_sha256 = digest(wheel.path())

  if sha256 and computed_sha256 != sha256:
    if resolving:
      if locally_built:
        # If we built the wheel locally and the sha256 had changed from the previous one,
        # build the wheel again to make sure we get the same digest again.
        os.rename(wheel.path(), wheel.path() + ".0")
        if pip_main(cmd, env):
          sys.exit(1)
        strip_wheel(wheel)
        second_sha256 = digest(wheel.path())
        if computed_sha256 != second_sha256:
          os.rename(wheel.path(), wheel.path() + ".1")
          print("Wheel build not deterministic:")
          print("   %s.0: %s" % (wheel.path(), computed_sha256))
          print("   %s.1: %s" % (wheel.path(), second_sha256))
          sys.exit(1)
        os.remove(wheel.path() + ".0")
    else:
      # If the user supplied an expected sha256, the built wheel should match it.
      print("\033[0;33mWARNING:\033[0m Built wheel %s digest %s does not match expected digest %s." % (wheel.path(), computed_sha256, sha256))

  shutil.rmtree(home)
  return computed_sha256

def get_cache_url(args):
  cache_base = os.environ.get("BAZEL_WHEEL_CACHE")
  if not cache_base or not args.cache_key:
    return None
  return "{}/{}".format(cache_base, args.cache_key)

def get_remote_retry_attempts():
  env_value = os.environ.get("BAZEL_WHEEL_REMOTE_RETRY_ATTEMPTS")
  if not env_value or env_value == '0':
    return 0
  else:
    return int(env_value)

def local_fallback_enabled():
  env_value = os.environ.get("BAZEL_WHEEL_LOCAL_FALLBACK")
  if env_value and env_value == '1':
    return True
  else:
    return False

def requests_with_retry(retries):
  session = requests.Session()
  # Retry on server and gateway errors as they may be intermittent.
  # Retry intervals are [0.0, 0.2, 0.4, 0.8, ...] seconds.
  retry = Retry(total=retries, backoff_factor=0.1, status_forcelist=(500, 502, 503, 504))
  adapter = HTTPAdapter(max_retries=retry)
  session.mount('http://', adapter)
  session.mount('https://', adapter)
  return session

def build(args):
  build_wheel(**vars(args))

parser = subparsers.add_parser('build', help='Download or build a single wheel, optionally checking from cache first')
parser.set_defaults(func=build)

parser.add_argument('--directory', action='store', default='.',
                    help=('The directory into which to put .whl file.'))

parser.add_argument('--cache-key', action='store',
                    help=('The cache key to use when looking up .whl file from cache.'))

parser.add_argument('--build-dir', action='store',
                    help=('A directory to build the wheel in, needs to be stable to keep the build deterministic (e.g. debug symbols).'))

parser.add_argument('--build-env', action='append', default=[],
                    help=('Environmental variables to set when building.'))

parser.add_argument('--build-deps', action='append', default=[],
                    help=('Wheels that are required to be installed when building.'))

parser.add_argument('--distribution', action='store',
                    help=('Name of the distribution to build.'))

parser.add_argument('--version', action='store',
                    help=('Version of the distribution to build.'))

parser.add_argument('--sha256', action='store',
                    help=('The expected sha256 digest of the built wheel.'))

parser.add_argument('--pip_arg', dest='pip_args', action='append', default=[],
                    help=('Extra arguments to send to pip.'))


# piptool extract
# ---------------

def extract(args):
  whl = Wheel(args.whl)
  whl.expand(args.directory)


parser = subparsers.add_parser('extract', help='Extract a wheel')
parser.set_defaults(func=extract)

parser.add_argument('--whl', action='store', required=True,
                    help=('The .whl file we are expanding.'))

parser.add_argument('--directory', action='store', default='.',
                    help='The directory into which to expand things.')


# piptool genbuild
# ---------------

def genbuild(args):
  whl = Wheel(args.whl)
  extra_deps = args.add_dependency or []
  drop_deps = {d: None for d in args.drop_dependency or []}

  external_deps = {d for d in itertools.chain(whl.dependencies(), extra_deps) if d not in drop_deps}

  additional_contents = []
  add_build_content = args.add_build_content or []
  for name in add_build_content:
      with open(name) as f:
          additional_contents.append(f.read() + '\n')
  additional_contents = '\n'.join(additional_contents)

  parser = whl.entrypoints()
  entrypoints_build = ''
  entrypoints_build2 = ''
  if parser:
      if parser.has_section('console_scripts'):
          for name, location in parser.items('console_scripts'):
              # Assumes it doesn't depend on extras. TODO(conrado): fix
              attrs = []
              attrs += [("name", '"%s"' % name)]
              attrs += [("entrypoint", '"%s"' % location)]
              attrs += [("deps", '[requirement("%s")]' % whl.name())]
              entrypoints_build2 += """
py_entrypoint_binary(
    {attrs}
)
""".format(attrs="\n    ".join(['{} = {},'.format(k, v) for k, v in attrs]))

  # If something got generated, add header.
  if entrypoints_build2:
    entrypoints_build2 = """\
load("@rules_python//python:python.bzl", "py_entrypoint_binary")

package(default_visibility = ["//visibility:public"])
""" + entrypoints_build2
    if "requirement(" in entrypoints_build2:
      entrypoints_build2 = """\
load("@{repository}//:requirements.bzl", "requirement")
""".format(repository=args.repository) + entrypoints_build2

  attrs = []
  if args.patches:
    attrs += [("patches", '["%s"]' % '", "'.join(args.patches))]
  if args.patch_tool:
    attrs += [("patch_tool", '"%s"' % args.patch_tool)]
  if args.patch_args:
    attrs += [("patch_args", '["%s"]' % '", "'.join(args.patch_args))]
  if args.patch_cmds:
    attrs += [("patch_cmds", '["%s"]' % '", "'.join(args.patch_cmds))]
  if args.wheel_repo:
    attrs += [("srcs", '["@%s//:wheel"]' % args.wheel_repo)]
  else:
    attrs += [("wheel", '"%s"' % whl.basename())]
  if args.python_version:
    attrs += [("python_version", '"%s"' % args.python_version)]
  if external_deps:
    deps = ''.join([
      ('\n        "%s",' % d) if d[0] == "@" else ('\n        requirement("%s"),' % d)
      for d in sorted(external_deps)
    ])
    attrs += [("deps", "[%s\n    ]" % deps)]

  if entrypoints_build2:
    os.mkdir(os.path.join(args.directory, 'bin'))
    with open(os.path.join(args.directory, 'bin', 'BUILD'), 'w') as f:
      f.write(entrypoints_build2)

  with open(os.path.join(args.directory, 'BUILD'), 'w') as f:
    contents = """\
load("@rules_python//python:python.bzl", "extract_wheel")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "{name}",
    {attrs},
)
""".format(name=whl.distribution().lower(),
           repository=args.repository,
           attrs=",\n    ".join(['{} = {}'.format(k, v) for k, v in attrs]),
    )
    if args.extras:
      contents += ''.join([
    """
py_library(
    name = "{extra}",
    deps = [
        ":{name}",{deps}
    ],
)
""".format(name=whl.distribution().lower(),
           extra=extra,
            deps=''.join([
                '\n        requirement("%s"),' % dep
                for dep in sorted(whl.dependencies(extra))
                if dep not in external_deps
              ]))
        for extra in args.extras or []
      ])
    if additional_contents:
      contents += additional_contents

    if "requirement(" in contents:
      contents = """\
load("@{repository}//:requirements.bzl", "requirement")
""".format(repository=args.repository) + contents

    f.write(contents)

parser = subparsers.add_parser('genbuild', help='Extract one or more wheels as a py_library')
parser.set_defaults(func=genbuild)

parser.add_argument('--whl', action='store', required=True,
                    help=('The .whl file we are expanding.'))

parser.add_argument('--wheel_repo', action='store',
                    help=('The repository name where the .whl file is.'))

parser.add_argument('--repository', action='store', required=True,
                    help='The pip_import from which to draw dependencies.')

parser.add_argument('--add-dependency', action='append',
                    help='Specify additional dependencies beyond the ones specified in the wheel.')

parser.add_argument('--drop-dependency', action='append',
                    help='Specify dependencies to ignore.')

parser.add_argument('--add-build-content', action='append',
                    help='Specify lines to add to the BUILD file.')

parser.add_argument('--directory', action='store', default='.',
                    help='The directory into which to expand things.')

parser.add_argument('--extras', action='append',
                    help='The set of extras for which to generate library targets.')

parser.add_argument('--python-version', action='store',
                    help='Specify python_version (PY2 or PY3) to set for the py_binary targets.')

parser.add_argument('--patches', action='append')
parser.add_argument('--patch-tool', action='store')
parser.add_argument('--patch-args', action='append')
parser.add_argument('--patch-cmds', action='append')


# piptool resolve
# ---------------

def determine_possible_extras(whls):
  """Determines the list of possible "extras" for each .whl

  The possibility of an extra is determined by looking at its
  additional requirements, and determinine whether they are
  satisfied by the complete list of available wheels.

  Args:
    whls: a list of Wheel objects

  Returns:
    a dict that is keyed by the Wheel objects in whls, and whose
    values are lists of possible extras.
  """
  whl_map = {
    whl.name(): whl
    for whl in whls
  }

  # TODO(mattmoor): Consider memoizing if this recursion ever becomes
  # expensive enough to warrant it.
  def is_possible(name, extra):
    # If we don't have the .whl at all, then this isn't possible.
    if name not in whl_map:
      return False
    whl = whl_map[name]
    # If we have the .whl, and we don't need anything extra then
    # we can satisfy this dependency.
    if not extra:
      return True
    # If we do need something extra, then check the extra's
    # dependencies to make sure they are fully satisfied.
    for extra_dep in whl.dependencies(extra=extra):
      req = pkg_resources.Requirement.parse(extra_dep)
      # Check that the dep and any extras are all possible.
      if not is_possible(req.project_name, None):
        return False
      for e in req.extras:
        if not is_possible(req.project_name, e):
          return False
    # If all of the dependencies of the extra are satisfiable then
    # it is possible to construct this dependency.
    return True

  return {
    whl: [
      extra
      for extra in whl.extras()
      if is_possible(whl.name(), extra)
    ]
    for whl in whls
  }

def build_dep_graph(input_files, build_info):
    pattern = re.compile('[a-zA-Z0-9_-]+')

    flatten = lambda l: [item for sublist in l for item in sublist]
    dist_to_lines = collections.defaultdict(list)
    for i in input_files:
        with open(i) as f:
            for l in f.readlines():
                l = l.strip()
                m = pattern.match(l)
                if m:
                    dist_to_lines[m.group()].append(l)

    if not build_info:
        return [flatten(dist_to_lines.values())]

    deps = collections.defaultdict(list)
    for dist, info in build_info.items():
      for d in info.get("additional_buildtime_deps", []):
        deps[dist] += dist_to_lines[d]

    graph = {r: set(deps[n]) if n in deps else set() for n,rr in dist_to_lines.items() for r in rr}
    result = list(toposort.toposort(graph))
    return result

def wheels_from_dir(dir):
  def list_whls(dir):
    for root, _, filenames in os.walk(dir + "/"):
      for fname in filenames:
        if fname.endswith('.whl'):
          yield Wheel(os.path.join(root, fname))
  whls = list(list_whls(dir))
  whls.sort(key=lambda x: x.name())
  return whls

def strip_wheel(w):
    ts = (1980, 1, 1, 0, 0, 0)
    tempdir = tempfile.mkdtemp()
    try:
      w.expand(tempdir)
      with zipfile.ZipFile(w.path(), 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(tempdir):
          dirs.sort()  # https://stackoverflow.com/questions/18282370/in-what-order-does-os-walk-iterates-iterate
          for f in sorted(files):
            local_path = os.path.join(root, f)
            with open(local_path, "rb") as ff:
              info = zipfile.ZipInfo(os.path.relpath(local_path, start=tempdir), ts)
              info.external_attr = (os.stat(local_path).st_mode & 0o777) << 16
              zipf.writestr(info, ff.read())
    finally:
      shutil.rmtree(tempdir)

def digest(fname):
  d = hashlib.sha256()
  with open(fname, "rb") as f:
    for chunk in iter(lambda: f.read(4096), b""):
      d.update(chunk)
  return d.hexdigest()

def resolve(args):
  print("Generating %s from %s..." % (args.output, " and ".join(args.input)))
  print(args)

  # Parse build_info - this is the contents of "requirements_overrides" attribute
  # passed by the user, serialized to json.
  build_info = json.loads(args.build_info or '{}')
  ordering = build_dep_graph(args.input, build_info)

  tempdir = tempfile.mkdtemp()

  existing_pythonpath = os.environ.get('PYTHONPATH', '')
  env = {}
  env['PYTHONPATH'] = tempdir + ':' + existing_pythonpath

  env["HOME"] = tempdir
  with open(os.path.join(tempdir, ".pydistutils.cfg"), "w") as f:
    # WAR for macOS: https://github.com/Homebrew/brew/issues/837
    f.write("[install]\nprefix=\n")

  # Process .pth files of the extracted build deps.
  with open(os.path.join(tempdir, "sitecustomize.py"), "w") as f:
    f.write("import site; import os; site.addsitedir(os.path.dirname(__file__))")

  downloaded_wheel_urls = {}
  for i, o in enumerate(ordering):
      # Install the wheels since they can be dependent at build time
      for _, _, filelist in os.walk(args.directory):
          filelist = [f for f in filelist if f.endswith('.whl')]
          filelist = [os.path.join(args.directory, f) for f in filelist]
          if filelist:
            pip_args = ["install", "-q", "--upgrade", "-t", tempdir] + filelist
            if pip_main(pip_args, env):
              shutil.rmtree(tempdir)
              sys.exit(1)

      with tempfile.NamedTemporaryFile(mode='w+') as f:
          with tempfile.NamedTemporaryFile(mode='w+') as f2:
              f.write('\n'.join(o))
              f.flush()

              f2.write('\n'.join(['\n'.join(c) for c in ordering]))
              f2.flush()

              pip_args = ["wheel"]
              #pip_args += ["--cache-dir", cache_dir]
              if args.directory:
                pip_args += ["-w", args.directory]
              #if args.input:
              #  pip_args += ["--requirement=" + i for i in args.input]
              pip_args += ["--requirement=" + f.name]
              pip_args += ["--constraint=" + f2.name]
              pip_args += args.pip_args
              with CaptureOutput() as output:
                if pip_main(pip_args, env):
                  print("pip command failed: " + str(pip_args))
                  shutil.rmtree(tempdir)
                  sys.exit(1)
                dls = re.findall(r'(?:Downloading|Using cached) (\S*\.whl)', output.stdout.getvalue().decode())
                downloaded_wheel_urls.update({
                  urllib.parse.unquote(url[url.rfind("/")+1 :]): url
                  for url in dls
                })

  shutil.rmtree(tempdir)

  # Enumerate the .whl files we downloaded.
  whls = wheels_from_dir(args.directory)

  possible_extras = determine_possible_extras(whls)

  def quote(string):
    return '"{}"'.format(string)

  whl_map = {
    whl.name(): whl
    for whl in whls
  }

  def transitive_deps(wheel, extra=None, collected=None, build_info=None):
    deps = wheel.dependencies(extra)
    if build_info:
      deps |= set(build_info.get(wheel.name(), {}).get("additional_runtime_deps", []))
    if collected is None:
      collected = set()
    for dep in deps.copy():
      if dep not in collected:
        collected.add(dep)
        d, extra = split_extra(dep)
        deps |= transitive_deps(whl_map[d], extra, collected, build_info)
    return deps

  def transitive_build_deps(wheel, build_info):
      deps = set()
      for build_dep in build_info.get(wheel.name(), {}).get("additional_buildtime_deps", []):
        # Add any packages mentioned explicitly in "additional_buildtime_deps".
        deps |= {whl_map[build_dep]}
        # Add any runtime deps of such packages.
        for runtime_dep_of_build_dep in transitive_deps(whl_map[build_dep], build_info=build_info):
          deps |= {whl_map[runtime_dep_of_build_dep]}
      return deps

  wheel_digests = {}
  try:
    with open(args.output, 'r') as f:
      contents = f.read()
      contents = re.sub(r".*^wheels = ", "", contents, flags=re.DOTALL|re.MULTILINE)
      # Need to use literal_eval, since this is bzl, not json (trailing commas, comments).
      wheel_info = ast.literal_eval(contents)
      wheel_digests.update({k: v["sha256"] for k, v in wheel_info.items() if "sha256" in v})
  except (ValueError, IOError):
    # If we can't parse the old wheel map, the remaining steps will be a bit slower.
    print("Failed to parse old wheel map, but this is OK.")

  # If user requested digests, we build each wheel again in isolation to get a
  # deterministic sha256.
  if args.digests:
    for w in whls:
      # If we downloaded a whl file instead of building it locally, we can use its digest as is.
      if w.basename() in downloaded_wheel_urls:
        wheel_digests[w.name()] = digest(w.path())
        continue

      # If the current (not-yet-updated) requirements.bzl already has a sha256 and it
      # matches with the sha of the wheel that we bulit during resolve (typical for
      # binary distributions), then we can just use that.
      resolved_digest = digest(w.path())
      if w.name() in wheel_digests:
        if resolved_digest == wheel_digests[w.name()]:
          continue

      build_deps = {w.path() for w in transitive_build_deps(w, build_info)}
      build_env = build_info.get(w.name(), {}).get("additional_buildtime_env", [])
      tempdir = tempfile.mkdtemp()
      try:
        sha256 = build_wheel(
          distribution=w.distribution(),
          version=build_info.get(w.name(), {}).get("version", w.version()),
          directory=tempdir,
          # NOTE: The build-dir here must match the one that we use in the
          # individual build_wheel() rules later, otherwise the sha256 that we
          # compute here will not match the output of build_wheel() due to debug
          # symbols.
          build_dir="/tmp/pip-build/%s_wheel" % w.repository_name(prefix=args.name),
          build_env=build_env,
          build_deps=build_deps,
          pip_args=args.pip_args,
          sha256=wheel_digests.get(w.name(), None),
          resolving=True,
        )
        wheel_digests[w.name()] = sha256
      finally:
        shutil.rmtree(tempdir)

  if args.output_format == 'download':
    # We are generating a checked-in version of requirements.bzl.
    # For determinism, avoid clashes with other pip_import repositories,
    # and prefix the current pip_import domain to the lib repo name.
    lib_repo = lambda w: w.repository_name(prefix=args.name)
    # Each wheel has its own repository that, refer to that.
    wheel_repo = lambda w: lib_repo(w) + '_wheel'
  else:
    # We are generating requirements.bzl to the bazel output area (legacy mode).
    # Use the good old 'pypi__' refix.
    lib_repo = lambda w: w.repository_name(prefix='pypi')
    # Wheels are downloaded to the pip_import repository, refer to that.
    wheel_repo = lambda w: args.name

  def whl_library(wheel):
    attrs = []
    attrs += [("name", quote(lib_repo(wheel)))]
    extras = ', '.join([quote(extra) for extra in sorted(possible_extras.get(wheel, []))])
    if extras != '':
      attrs += [("extras", '[{}]'.format(extras))]
    if args.digests:
      attrs += [("sha256", quote(wheel_digests[wheel.name()]))]
    url = downloaded_wheel_urls.get(wheel.basename(), None)
    if url:
      attrs += [("urls", '[{}]'.format(quote(url)))]
    attrs += [("version", quote(wheel.version()))]
    attrs += [("wheel_name", quote(wheel.basename()))]
    if args.output_format != 'download':
      attrs += [("wheel", '"@{}//:{}"'.format(args.name, wheel.basename()))]
    build_deps = {w.name() for w in transitive_build_deps(wheel, build_info)}
    build_deps = ', '.join([quote(dep) for dep in sorted(build_deps)])
    if build_deps != '':
      attrs += [("build_deps", '[{}]'.format(build_deps))]

    return """"{}": {{
        {},
    }},""".format(wheel.name(), ",\n        ".join(['"{}": {}'.format(k, v) for k, v in attrs]))

  if args.output_dir:
    os.makedirs(args.output_dir, exist_ok=True)
    _, subdirs, _ = next(os.walk(args.output_dir))
    for subdir in subdirs:
      shutil.rmtree(os.path.join(args.output_dir, subdir))
    with open(os.path.join(args.output_dir, "BUILD"), "w"): pass
    for w in whls:
      buildfile_dir = os.path.join(args.output_dir, w.distribution().lower())
      os.makedirs(buildfile_dir)
      genbuild_args = argparse.Namespace(
        directory=buildfile_dir,
        repository=args.name,
        whl=w.path(),
        wheel_repo=wheel_repo(w),
        add_dependency=None,
        drop_dependency=None,
        add_build_content=None,
        extras=sorted(possible_extras.get(w, [])),
        python_version=None,
        patches=None,
        patch_tool=None,
        patch_args=None,
        patch_cmds=None,
      )
      print("Generating BUILD file to %s from %s" % (buildfile_dir, w.path()))
      genbuild(genbuild_args)

  with open(args.output, 'w') as f:
    f.write('""" Install pip requirements. """' + """

{comment}
wheels = {{
    {wheels}
}}
""".format(comment='\n'.join(['# Generated from ' + i for i in args.input]),
           wheels='\n    '.join(map(whl_library, whls))))

parser = subparsers.add_parser('resolve', help='Resolve requirements.bzl from requirements.txt')
parser.set_defaults(func=resolve)

parser.add_argument('--name', action='store', required=True,
                    help=('The namespace of the import.'))

parser.add_argument('--build-info', action='store',
                    help=('Additional build info as a string-serialized python dict.'))

parser.add_argument('--input', action='append', required=True,
                    help=('The requirements.txt file(s) to import.'))

parser.add_argument('--output', action='store', required=True,
                    help=('The requirements.bzl file to export.'))

parser.add_argument('--output-dir', action='store',
                    help=('The directory under which to generate BUILD files.'))

parser.add_argument('--output-format', choices=['refer', 'download'], default='refer',
                    help=('How whl_library rules should obtain the wheel.'))

parser.add_argument('--directory', action='store', default='.',
                    help=('The directory into which to put .whl files.'))

parser.add_argument('--digests', action='store_true',
                    help=('Emit sha256 digests for the bulit wheels, and ensure deterministic build.'))

parser.add_argument('--pip-arg', dest='pip_args', action='append', default=[],
                    help=('Extra arguments to send to pip.'))


def main():
  args = global_parser.parse_args()
  f = args.func
  del args.func
  f(args)

if __name__ == '__main__':
  main()
