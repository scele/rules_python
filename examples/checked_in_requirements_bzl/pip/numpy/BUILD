load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "numpy",
    version = "1.16.5",
    wheel = "@examples_checked_in_requirements_bzl__numpy_1_16_5//:numpy-1.16.5-cp27-cp27mu-manylinux1_x86_64.whl",
    wheel_size = 17004063,
)

py_binary(
    name = "f2py",
    srcs = ["entrypoint_f2py.py"],
    main = "entrypoint_f2py.py",
    deps = [":pkg"]
)

py_binary(
    name = "f2py2",
    srcs = ["entrypoint_f2py2.py"],
    main = "entrypoint_f2py2.py",
    deps = [":pkg"]
)

py_binary(
    name = "f2py2.7",
    srcs = ["entrypoint_f2py2.7.py"],
    main = "entrypoint_f2py2.7.py",
    deps = [":pkg"]
)
