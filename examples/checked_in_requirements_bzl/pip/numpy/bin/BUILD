load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_entrypoint_binary")

package(default_visibility = ["//visibility:public"])

py_entrypoint_binary(
    name = "f2py",
    entrypoint = "numpy.f2py.f2py2e:main",
    deps = [requirement("numpy")],
)

py_entrypoint_binary(
    name = "f2py2",
    entrypoint = "numpy.f2py.f2py2e:main",
    deps = [requirement("numpy")],
)

py_entrypoint_binary(
    name = "f2py2.7",
    entrypoint = "numpy.f2py.f2py2e:main",
    deps = [requirement("numpy")],
)
