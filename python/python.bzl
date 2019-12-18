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

WheelInfo = provider(
    fields = {
        "wheel": "wheel (File)",
        "size": "size of the wheel in bytes (int)",
    },
)

def py_library(*args, **kwargs):
  """See the Bazel core py_library documentation.

  [available here](
  https://docs.bazel.build/versions/master/be/python.html#py_library).
  """
  native.py_library(*args, **kwargs)

def py_binary(*args, **kwargs):
  """See the Bazel core py_binary documentation.

  [available here](
  https://docs.bazel.build/versions/master/be/python.html#py_binary).
  """
  native.py_binary(*args, **kwargs)

def py_test(*args, **kwargs):
  """See the Bazel core py_test documentation.

  [available here](
  https://docs.bazel.build/versions/master/be/python.html#py_test).
  """
  native.py_test(*args, **kwargs)

def _extract_wheel_impl(ctx):
    if ctx.attr.srcs:
        wheelInfo = ctx.attr.srcs[0][WheelInfo]
        wheel = wheelInfo.wheel
    else:
        wheelInfo = WheelInfo()
        wheel = ctx.file.wheel
    libdir = ctx.actions.declare_directory("lib")
    command = ["BUILDDIR=$(pwd)"]
    command += ["%s extract --whl=%s --directory=%s" % (ctx.executable._piptool.path, wheel.path, libdir.path)]
    inputs = [wheel]
    outputs = [libdir]
    tools = [ctx.executable._piptool]

    command += ["cd %s" % libdir.path]
    for patchfile in ctx.files.patches:
        command += ["{patchtool} {patch_args} < $BUILDDIR/{patchfile}".format(
            patchtool = ctx.attr.patch_tool,
            patchfile = patchfile.path,
            patch_args = " ".join([
                "'%s'" % arg
                for arg in ctx.attr.patch_args
            ]),
        )]
        inputs += [patchfile]

    command += ctx.attr.patch_cmds

    ctx.actions.run_shell(
        inputs = inputs,
        outputs = outputs,
        tools = tools,
        command = " && ".join(command),
        mnemonic = "ExtractWheel",
    )

    has_py2_only_sources = ctx.attr.python_version == "PY2"
    has_py3_only_sources = ctx.attr.python_version == "PY3"
    if not has_py2_only_sources:
        for d in ctx.attr.deps:
            if d[PyInfo].has_py2_only_sources:
                has_py2_only_sources = True
                break
    if not has_py3_only_sources:
        for d in ctx.attr.deps:
            if d[PyInfo].has_py3_only_sources:
                has_py3_only_sources = True
                break
    if ctx.label.workspace_name:
        imp = libdir.short_path[3:]
    else:
        imp = "%s/%s" % (ctx.workspace_name, libdir.short_path)
    imports = depset(direct = [imp], transitive = [d[PyInfo].imports for d in ctx.attr.deps] + [ctx.attr._site[PyInfo].imports])
    transitive_sources = depset(direct = [libdir], transitive = [d[PyInfo].transitive_sources for d in ctx.attr.deps] + [ctx.attr._site[PyInfo].transitive_sources])
    runfiles = ctx.runfiles(files = [libdir])
    for d in ctx.attr.deps:
        runfiles = runfiles.merge(d[DefaultInfo].default_runfiles)
    runfiles = runfiles.merge(ctx.attr._site[DefaultInfo].default_runfiles)
    return [
        DefaultInfo(
            files = depset(direct = outputs),
            runfiles = runfiles,
        ),
        wheelInfo,
        PyInfo(
            imports = imports,
            transitive_sources = transitive_sources,
            has_py2_only_sources = has_py2_only_sources,
            has_py3_only_sources = has_py3_only_sources,
        ),
    ]

extract_wheel = rule(
    implementation = _extract_wheel_impl,
    attrs = {
        "wheel": attr.label(
            doc = "A wheel to extract.",
            allow_single_file = [".whl"],
        ),
        "srcs": attr.label_list(
            doc = "A wheel to extract.",
            providers = [WheelInfo],
        ),
        "imports": attr.string_list(),
        "deps": attr.label_list(providers=[PyInfo]),
        "patches": attr.label_list(default = [], allow_files=True),
        "patch_tool": attr.string(default = "patch"),
        "patch_args": attr.string_list(default = ["-p0"]),
        "patch_cmds": attr.string_list(default = []),
        "python_version": attr.string(values = ["PY2", "PY3", ""]),
        "_piptool": attr.label(
            allow_files = True,
            executable = True,
            default = Label("//tools:piptool.par"),
            cfg = "host",
        ),
        "_site": attr.label(
            providers = [PyInfo],
            default = Label("@io_bazel_rules_python//python:site"),
        ),
    },
)


def py_entrypoint_binary(name, entrypoint, **kwargs):
    parts = entrypoint.split(":", 2)
    entrypoint_name = "_%s.py" % name
    native.genrule(
        name = "gen_" + name,
        outs = [entrypoint_name],
        cmd = "echo 'import sys; from %s import %s as main; sys.exit(main())' > $@" % (parts[0], parts[1]),
    )
    py_binary(
        name = name,
        srcs = [entrypoint_name],
        main = entrypoint_name,
        **kwargs
    )

def _prebuilt_wheel_impl(ctx):
    return [
        WheelInfo(
            wheel = ctx.files.srcs[0],
            size = ctx.attr.size,
        ),
    ]

prebuilt_wheel = rule(
    attrs = {
        "srcs": attr.label_list(allow_files = [".whl"]),
        "size": attr.int(),
    },
    implementation = _prebuilt_wheel_impl,
)
