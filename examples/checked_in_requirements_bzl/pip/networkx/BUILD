load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "extract_wheel")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "networkx",
    srcs = ["@examples_checked_in_requirements_bzl__networkx_2_2_wheel//:wheel"],
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
