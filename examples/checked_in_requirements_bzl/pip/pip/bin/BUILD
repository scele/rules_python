load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_entrypoint_binary")

package(default_visibility = ["//visibility:public"])

py_entrypoint_binary(
    name = "pip",
    entrypoint = "pip:main",
    deps = [requirement("pip")],
)

py_entrypoint_binary(
    name = "pip3",
    entrypoint = "pip:main",
    deps = [requirement("pip")],
)

py_entrypoint_binary(
    name = "pip3.5",
    entrypoint = "pip:main",
    deps = [requirement("pip")],
)
