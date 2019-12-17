load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "pytz",
    version = "2019.3",
    wheel = "@examples_checked_in_requirements_bzl__pytz_2019_3//:pytz-2019.3-py2.py3-none-any.whl",
    wheel_size = 509158,
)
