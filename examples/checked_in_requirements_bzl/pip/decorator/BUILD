load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "decorator",
    srcs = ["@examples_checked_in_requirements_bzl__decorator_4_4_2_wheel//:wheel"],
)
