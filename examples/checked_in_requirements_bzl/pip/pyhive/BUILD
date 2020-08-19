load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement", "wheel")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pyhive",
    srcs = [wheel("pyhive")],
    deps = [
        requirement("future"),
        requirement("python-dateutil"),
    ],
)

py_library(
    name = "sqlalchemy",
    deps = [
        ":pyhive",
        requirement("sqlalchemy"),
    ],
)
