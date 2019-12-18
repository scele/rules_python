load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    srcs = ["@examples_checked_in_requirements_bzl__networkx_2_2_wheel//:wheel"],
    deps = [
        requirement("decorator"),
    ],
)

py_library(
    name = "numpy",
    deps = [
        ":pkg",
        requirement("decorator"),
        requirement("numpy"),
    ],
)

py_library(
    name = "pandas",
    deps = [
        ":pkg",
        requirement("decorator"),
        requirement("pandas"),
    ],
)
