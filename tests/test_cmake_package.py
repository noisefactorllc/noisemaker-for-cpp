import os
from pathlib import Path
import subprocess
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONSUMER_ROOT = REPOSITORY_ROOT / "tests" / "cmake_package_consumer"


class CMakePackageTests(unittest.TestCase):
    def test_installed_package_builds_external_consumer(self):
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"

        with tempfile.TemporaryDirectory(prefix="noisemaker-cmake-package-") as raw:
            run_root = Path(raw)
            build_root = run_root / "build"
            install_root = run_root / "prefix"
            consumer_build_root = run_root / "consumer-build"

            self._run(
                [
                    "cmake",
                    "-S",
                    str(REPOSITORY_ROOT),
                    "-B",
                    str(build_root),
                    "-DCMAKE_BUILD_TYPE=Release",
                    f"-DCMAKE_INSTALL_PREFIX={install_root}",
                ],
                environment,
            )
            self._run(
                ["cmake", "--build", str(build_root), "--target", "noisemaker-cpu", "--parallel"],
                environment,
            )
            self._run(["cmake", "--install", str(build_root)], environment)

            self.assertTrue(
                (install_root / "lib/cmake/noisemaker-for-cpp/noisemaker-for-cppConfig.cmake").is_file()
            )
            self.assertTrue(
                (install_root / "include/noisemaker/generated/catalog.hpp").is_file()
            )

            self._run(
                [
                    "cmake",
                    "-S",
                    str(CONSUMER_ROOT),
                    "-B",
                    str(consumer_build_root),
                    "-DCMAKE_BUILD_TYPE=Release",
                    f"-DCMAKE_PREFIX_PATH={install_root}",
                ],
                environment,
            )
            self._run(["cmake", "--build", str(consumer_build_root), "--parallel"], environment)
            self._run([str(consumer_build_root / "noisemaker-package-consumer")], environment)

    @staticmethod
    def _run(command, environment):
        subprocess.run(command, check=True, env=environment)


if __name__ == "__main__":
    unittest.main()
