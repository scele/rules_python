load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pkg",
    distribution = "pandas",
    version = "0.24.2",
    wheel = "@examples_checked_in_requirements_bzl__pandas_0_24_2//:pandas-0.24.2-cp27-cp27mu-manylinux1_x86_64.whl",
    wheel_size = 10116426,
    deps = [
        requirement("numpy"),
        requirement("python-dateutil"),
        requirement("pytz"),
    ],
)
