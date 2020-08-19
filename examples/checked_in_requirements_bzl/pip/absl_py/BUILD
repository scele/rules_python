load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "extract_wheel")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "absl_py",
    srcs = ["@examples_checked_in_requirements_bzl__absl_py_0_7_0_wheel//:wheel"],
    deps = [
        requirement("enum34"),
        requirement("six"),
    ],
)
