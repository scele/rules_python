load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "absl_py",
    version = "0.7.0",
    wheel = "@examples_checked_in_requirements_bzl__absl_py_0_7_0//:absl_py-0.7.0-py2-none-any.whl",
    wheel_size = 113528,
    deps = [
        requirement("enum34"),
        requirement("six"),
    ],
)
