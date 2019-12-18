load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    srcs = ["@examples_checked_in_requirements_bzl__PyHive_0_6_1_wheel//:wheel"],
    deps = [
        requirement("future"),
        requirement("python-dateutil"),
    ],
)

py_library(
    name = "sqlalchemy",
    deps = [
        ":pkg",
        requirement("future"),
        requirement("python-dateutil"),
        requirement("sqlalchemy"),
    ],
)
