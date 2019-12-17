load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "pip",
    version = "9.0.0",
    wheel = "@examples_checked_in_requirements_bzl__pip_9_0_0//:pip-9.0.0-py2.py3-none-any.whl",
    wheel_size = 1254648,
)

py_binary(
    name = "pip",
    srcs = ["entrypoint_pip.py"],
    main = "entrypoint_pip.py",
    deps = [":pkg"]
)

py_binary(
    name = "pip3",
    srcs = ["entrypoint_pip3.py"],
    main = "entrypoint_pip3.py",
    deps = [":pkg"]
)

py_binary(
    name = "pip3.5",
    srcs = ["entrypoint_pip3.5.py"],
    main = "entrypoint_pip3.5.py",
    deps = [":pkg"]
)
