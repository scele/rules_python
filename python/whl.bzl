# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Import .whl files into Bazel."""

load(
    "@bazel_tools//tools/build_defs/hash:hash.bzl",
    _hash_tools = "tools",
    _sha256 = "sha256",
)

load("@bazel_tools//tools/build_defs/repo:utils.bzl", "patch")
load("//python:version_check.bzl", "parse_bazel_version")

def _report_progress(ctx, status):
    if parse_bazel_version(native.bazel_version) >= parse_bazel_version("0.21"):
        ctx.report_progress(status)


def _extract_wheel(ctx, wheel):
    python = ctx.path(ctx.attr.python) if ctx.attr.python else "python"
    args = [
        python,
        ctx.path(ctx.attr._piptool),
        "genbuild",
        "--directory", str(ctx.path("")),
        "--repository", ctx.attr.repository,
    ]

    args += ["--whl=%s" % wheel]
    args += ["--add-dependency=%s" % d for d in ctx.attr.additional_runtime_deps]
    args += ["--drop-dependency=%s" % d for d in ctx.attr.remove_runtime_deps]
    if ctx.attr.additional_build_content:
        args += ["--add-build-content=%s" % ctx.path(ctx.attr.additional_build_content)]
    args += ["--extras=%s" % extra for extra in ctx.attr.extras]
    if ctx.attr.python_version:
        args += ["--python-version=%s" % ctx.attr.python_version]

    # Add our sitecustomize.py that ensures all .pth files are run.
    args += ["--add-dependency=@rules_python//python:site"]

    for x in ctx.attr.patches:
        args += ["--patches=@%s" % x]
    if ctx.attr.patch_tool:
        args += ["--patch-tool=%s" % ctx.attr.patch_tool]
    for x in ctx.attr.patch_args:
        args += ["--patch-args=%s" % x]
    for x in ctx.attr.patch_cmds:
        args += ["--patch-cmds=%s" % x]

    _report_progress(ctx, "Genbuild")
    result = ctx.execute(args, quiet=False)
    if result.return_code:
        fail("wheel genbuild failed: %s (%s)" % (result.stdout, result.stderr))


def _build_wheel(ctx):
    python = ctx.path(ctx.attr.python) if ctx.attr.python else "python"

    # Resolve the paths to the dependency wheels to force them to be created.
    # This may cause re-starting this repository rule, see:
    #  https://docs.bazel.build/versions/master/skylark/repository_rules.html#when-is-the-implementation-function-executed
    paths = [ctx.path(d) for d in ctx.attr.build_deps]

    # Check that python headers are installed. Otherwise some wheels may be built
    # differently depending on the machine..
    result = ctx.execute(["/bin/sh", "-c", "\n".join([
        "INCLUDEPY=$(%s -c \"import sysconfig; print(sysconfig.get_config_vars()['INCLUDEPY'])\")" % python,
        "ls \"$INCLUDEPY/Python.h\""
    ])])
    if result.return_code:
        fail(("Python headers not installed: %s" +
              "If you are using host machine's python interpreter, you may need to install headers from your OS vendor " +
              "(e.g. \"apt-get install python-dev python3-dev\" on Ubuntu).") % result.stderr)

    cmd = [
        "env", "-",
        python,
        ctx.path(ctx.attr._piptool),
        "build",
        "--directory", ctx.path(""),
        "--distribution", ctx.attr.distribution,
        "--version", ctx.attr.version,
        # Build the wheel in a deterministic path so that any debug symbols have stable
        # paths and the resulting wheel has a higher chance of being deterministic.
        "--build-dir", "/tmp/pip-build/%s" % ctx.name,
    ] + [
        "--build-env=%s" % x for x in ctx.attr.additional_buildtime_env
    ] + [
        "--build-deps=%s" % ctx.path(x) for x in ctx.attr.build_deps
    ] + [
        "--pip_arg=%s" % a for a in ctx.attr.pip_args
    ]
    if ctx.attr.sha256:
        cmd += ["--sha256", ctx.attr.sha256]

    _report_progress(ctx, "Building")
    result = ctx.execute(cmd, quiet=False)
    if result.return_code:
        fail("pip wheel failed: %s (%s)" % (result.stdout, result.stderr))

def _download_or_build_wheel_impl(ctx):
    """Core implementation of download_or_build_wheel."""

    if ctx.attr.local_path:
        ctx.symlink(ctx.attr.local_path, ctx.attr.wheel_name)
    elif ctx.attr.urls:
        ret = ctx.download(url=ctx.attr.urls, sha256=ctx.attr.sha256, output=ctx.attr.wheel_name, allow_fail=True)
        if not ret.success:
            _build_wheel(ctx)
    else:
        _build_wheel(ctx)

    result = ctx.execute(["stat", "--printf=%s", ctx.attr.wheel_name])
    if result.return_code:
        fail("whl not found: %s (%s)" % (result.stdout, result.stderr))
    ctx.file("BUILD", """\
load("@rules_python//python:python.bzl", "prebuilt_wheel")

exports_files(["{file}"])

prebuilt_wheel(
    name = "wheel",
    srcs = ["{file}"],
    size = {size},
    visibility = ["//visibility:public"],
)
""".format(file=ctx.attr.wheel_name, size=result.stdout.strip()))


_download_or_build_wheel_attrs = {
    "distribution": attr.string(),
    "version": attr.string(),
    "urls": attr.string_list(),
    "sha256": attr.string(),
    "local_path": attr.string(),
    "build_deps": attr.label_list(
        allow_files=["*.whl"],
    ),
    "additional_buildtime_env": attr.string_list(),
    "wheel_name": attr.string(),
    "pip_args": attr.string_list(),
    "python": attr.label(
        executable = True,
        cfg = "host",
    ),
    "_piptool": attr.label(
        executable = True,
        default = Label("//tools:piptool.par"),
        cfg = "host",
    ),
}


download_or_build_wheel = repository_rule(
    attrs = _download_or_build_wheel_attrs,
    implementation = _download_or_build_wheel_impl,
)

def _extract_wheel_impl(ctx):
    """Core implementation of extract_wheel."""
    ctx.symlink(ctx.attr.wheel, ctx.attr.wheel.name)
    _extract_wheel(ctx, ctx.path(ctx.attr.wheel))

_extract_wheel_attrs = {
    "wheel": attr.label(allow_files = True),
    "additional_runtime_deps": attr.string_list(),
    "additional_build_content":  attr.label(allow_single_file=True),
    "remove_runtime_deps": attr.string_list(),
    "patches": attr.label_list(default = []),
    "patch_tool": attr.string(default = "patch"),
    "patch_args": attr.string_list(default = ["-p0"]),
    "patch_cmds": attr.string_list(default = []),
    "repository":  attr.string(),
    "extras": attr.string_list(),
    "python_version": attr.string(values = ["PY2", "PY3", ""]),
    "python": attr.label(
        executable = True,
        cfg = "host",
    ),
    "_piptool": attr.label(
        executable = True,
        default = Label("//tools:piptool.par"),
        cfg = "host",
    ),
}

extract_wheel = repository_rule(
    attrs = _extract_wheel_attrs,
    implementation = _extract_wheel_impl,
)


"""A rule for importing <code>.whl</code> dependencies into Bazel.

<b>This rule is currently used to implement <code>pip_import</code>,
it is not intended to work standalone, and the interface may change.</b>
See <code>pip_import</code> for proper usage.

This rule imports a <code>.whl</code> file as a <code>py_library</code>:
<pre><code>whl_library(
    name = "foo",
    whl = ":my-whl-file",
    repository = "name of pip_import rule",
)
</code></pre>

This rule defines a <code>@foo//:pkg</code> <code>py_library</code> target.

Args:
  whl: The path to the .whl file (the name is expected to follow [this
    convention](https://www.python.org/dev/peps/pep-0427/#file-name-convention))

  requirements: The name of the pip_import repository rule from which to
    load this .whl's dependencies.

  extras: A subset of the "extras" available from this <code>.whl</code> for which
    <code>requirements</code> has the dependencies.
"""

wheel_rules = struct(
    download_or_build_wheel = struct(
        attrs = _download_or_build_wheel_attrs,
    ),
    extract_wheel = struct(
        attrs = _extract_wheel_attrs,
    ),
)
