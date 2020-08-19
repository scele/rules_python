load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "extract_wheel")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "python_dateutil",
    srcs = ["@examples_checked_in_requirements_bzl__python_dateutil_2_8_1_wheel//:wheel"],
    deps = [
        requirement("six"),
    ],
)
