load("@io_bazel_rules_python//python:python.bzl", "extract_wheel")
load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement", "wheel")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "networkx",
    srcs = [wheel("networkx")],
    deps = [
        requirement("decorator"),
    ],
)

py_library(
    name = "numpy",
    deps = [
        ":networkx",
        requirement("numpy"),
    ],
)

py_library(
    name = "pandas",
    deps = [
        ":networkx",
        requirement("pandas"),
    ],
)
