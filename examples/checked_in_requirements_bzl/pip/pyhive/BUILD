load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "pyhive",
    version = "0.6.1",
    wheel = "@examples_checked_in_requirements_bzl__PyHive_0_6_1//:PyHive-0.6.1-py2-none-any.whl",
    wheel_size = 46279,
    deps = [
        requirement("future"),
        requirement("python-dateutil"),
    ],
)
