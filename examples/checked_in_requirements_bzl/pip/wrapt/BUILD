load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "wrapt",
    version = "1.11.1",
    wheel = "@examples_checked_in_requirements_bzl__wrapt_1_11_1//:wrapt-1.11.1-cp27-cp27mu-linux_x86_64.whl",
    wheel_size = 64750,
)
