load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "networkx",
    version = "2.2",
    wheel = "@examples_checked_in_requirements_bzl__networkx_2_2//:networkx-2.2-py2.py3-none-any.whl",
    wheel_size = 1527322,
    deps = [
        requirement("decorator"),
    ],
)
