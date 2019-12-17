load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "python_dateutil",
    version = "2.8.1",
    wheel = "@examples_checked_in_requirements_bzl__python_dateutil_2_8_1//:python_dateutil-2.8.1-py2.py3-none-any.whl",
    wheel_size = 227183,
    deps = [
        requirement("six"),
    ],
)
