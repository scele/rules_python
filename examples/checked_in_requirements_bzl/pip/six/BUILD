load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "six",
    version = "1.13.0",
    wheel = "@examples_checked_in_requirements_bzl__six_1_13_0//:six-1.13.0-py2.py3-none-any.whl",
    wheel_size = 10747,
)
