load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "sqlalchemy",
    version = "1.1.15",
    wheel = "@examples_checked_in_requirements_bzl__SQLAlchemy_1_1_15//:SQLAlchemy-1.1.15-cp27-cp27mu-linux_x86_64.whl",
    wheel_size = 1087576,
)
