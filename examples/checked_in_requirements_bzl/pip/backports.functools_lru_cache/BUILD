load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "backports.functools_lru_cache",
    version = "1.5",
    wheel = "@examples_checked_in_requirements_bzl__backports_functools_lru_cache_1_5//:backports.functools_lru_cache-1.5-py2.py3-none-any.whl",
    wheel_size = 7007,
)
