load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    srcs = ["@examples_checked_in_requirements_bzl__absl_py_0_7_0_wheel//:wheel"],
    deps = [
        requirement("enum34"),
        requirement("six"),
    ],
)
