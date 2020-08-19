load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pytz",
    srcs = ["@examples_checked_in_requirements_bzl__pytz_2020_1_wheel//:wheel"],
)
