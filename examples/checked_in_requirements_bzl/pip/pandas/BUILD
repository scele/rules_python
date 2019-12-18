load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    srcs = ["@examples_checked_in_requirements_bzl__pandas_0_24_2_wheel//:wheel"],
    deps = [
        requirement("numpy"),
        requirement("python-dateutil"),
        requirement("pytz"),
    ],
)
