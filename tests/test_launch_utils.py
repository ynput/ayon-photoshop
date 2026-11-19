import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "client"
    / "ayon_photoshop"
    / "api"
    / "launch_utils.py"
)
SPEC = importlib.util.spec_from_file_location("launch_utils", MODULE_PATH)
launch_utils = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launch_utils)


class GetMacosLaunchArgsTest(unittest.TestCase):
    def test_keeps_native_arguments_for_universal_photoshop(self):
        args, arch = launch_utils.get_macos_launch_args(
            ["/Applications/Adobe Photoshop/Photoshop"],
            ["x86_64", "arm64"],
            {"arm64"},
        )

        self.assertEqual(
            args,
            ["/Applications/Adobe Photoshop/Photoshop"],
        )
        self.assertIsNone(arch)

    def test_uses_rosetta_for_x86_only_photoshop(self):
        args, arch = launch_utils.get_macos_launch_args(
            ["/Applications/Adobe Photoshop/Photoshop", "--flag"],
            ["x86_64"],
            {"arm64"},
        )

        self.assertEqual(
            args,
            [
                "arch",
                "-x86_64",
                "/Applications/Adobe Photoshop/Photoshop",
                "--flag",
            ],
        )
        self.assertEqual(arch, "x86_64")

    def test_keeps_arguments_when_architecture_detection_fails(self):
        original_args = ["/Applications/Adobe Photoshop/Photoshop"]

        args, arch = launch_utils.get_macos_launch_args(
            original_args,
            [],
            {"arm64"},
        )

        self.assertEqual(args, original_args)
        self.assertIsNone(arch)
        self.assertIsNot(args, original_args)

    def test_keeps_arguments_when_process_architecture_is_unknown(self):
        original_args = ["/Applications/Adobe Photoshop/Photoshop"]

        args, arch = launch_utils.get_macos_launch_args(
            original_args,
            ["x86_64", "arm64"],
            set(),
        )

        self.assertEqual(args, original_args)
        self.assertIsNone(arch)


if __name__ == "__main__":
    unittest.main()
