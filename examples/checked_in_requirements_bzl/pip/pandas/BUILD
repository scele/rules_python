load("@examples_checked_in_requirements_bzl//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "extract_wheel")

package(default_visibility = ["//visibility:public"])

extract_wheel(
    name = "pandas",
    srcs = ["@examples_checked_in_requirements_bzl__pandas_0_24_2_wheel//:wheel"],
    deps = [
        requirement("numpy"),
        requirement("python-dateutil"),
        requirement("pytz"),
    ],
)
