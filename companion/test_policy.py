#!/usr/bin/env python3
"""Run the native guard's pure policy tests without Gradle or Minecraft jars."""

from pathlib import Path
import os
import shutil
import subprocess
import tempfile


def main() -> None:
    root = Path(__file__).resolve().parent
    java_home = os.environ.get("JAVA_HOME")
    executable_suffix = ".exe" if os.name == "nt" else ""
    if java_home:
        javac = str(Path(java_home) / "bin" / ("javac" + executable_suffix))
        java = str(Path(java_home) / "bin" / ("java" + executable_suffix))
    else:
        javac = shutil.which("javac")
        java = shutil.which("java")
    if not javac or not java:
        raise SystemExit("A Java 21 JDK is required; set JAVA_HOME to its directory.")
    sources = [
        root / "src/main/java/ua/aia2/guard/GuardPolicy.java",
        root / "src/main/java/ua/aia2/guard/LiveTeamResolver.java",
        root / "src/main/java/ua/aia2/guard/RecipeIdentityIndex.java",
        root / "src/main/java/ua/aia2/guard/ScopedRecipeOwner.java",
        root / "src/policyTest/java/ua/aia2/guard/GuardPolicyTest.java",
        root / "src/policyTest/java/ua/aia2/guard/LiveTeamResolverTest.java",
        root / "src/policyTest/java/ua/aia2/guard/RecipeIdentityIndexTest.java",
        root / "src/policyTest/java/ua/aia2/guard/ScopedRecipeOwnerTest.java",
    ]
    with tempfile.TemporaryDirectory(prefix="aia2-policy-test-") as temporary:
        subprocess.run([javac, "--release", "21", "-encoding", "UTF-8", "-d", temporary,
                        *map(str, sources)], check=True)
        subprocess.run([java, "-cp", temporary, "ua.aia2.guard.GuardPolicyTest"], check=True)


if __name__ == "__main__":
    main()
