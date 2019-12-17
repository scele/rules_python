load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "scipy",
    version = "1.1.0",
    wheel = "@examples_checked_in_requirements_bzl__scipy_1_1_0//:scipy-1.1.0-cp27-cp27mu-manylinux1_x86_64.whl",
    wheel_size = 30828433,
    deps = [
        requirement("numpy"),
    ],
)
