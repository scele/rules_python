load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    srcs = ["@examples_checked_in_requirements_bzl__backports_ssl_match_hostname_3_5_0_1_wheel//:wheel"],
)
