load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "enum34",
    version = "1.1.6",
    wheel = "@examples_checked_in_requirements_bzl__enum34_1_1_6//:enum34-1.1.6-py2-none-any.whl",
    wheel_size = 12427,
)
