load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "decorator",
    version = "4.4.1",
    wheel = "@examples_checked_in_requirements_bzl__decorator_4_4_1//:decorator-4.4.1-py2.py3-none-any.whl",
    wheel_size = 9246,
)
