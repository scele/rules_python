load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "jsonnet",
    version = "0.11.2",
    wheel = "@examples_checked_in_requirements_bzl__jsonnet_0_11_2//:jsonnet-0.11.2-cp27-cp27mu-linux_x86_64.whl",
    wheel_size = 2895723,
)
