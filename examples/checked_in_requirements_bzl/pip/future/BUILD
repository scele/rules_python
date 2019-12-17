load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "future",
    version = "0.18.2",
    wheel = "@examples_checked_in_requirements_bzl__future_0_18_2//:future-0.18.2-py2-none-any.whl",
    wheel_size = 502566,
)

py_binary(
    name = "futurize",
    srcs = ["entrypoint_futurize.py"],
    main = "entrypoint_futurize.py",
    deps = [":pkg"]
)

py_binary(
    name = "pasteurize",
    srcs = ["entrypoint_pasteurize.py"],
    main = "entrypoint_pasteurize.py",
    deps = [":pkg"]
)
