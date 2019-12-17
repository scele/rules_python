load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "backports.ssl_match_hostname",
    version = "3.5.0.1",
    wheel = "@examples_checked_in_requirements_bzl__backports_ssl_match_hostname_3_5_0_1//:backports.ssl_match_hostname-3.5.0.1-py2-none-any.whl",
    wheel_size = 5210,
)
