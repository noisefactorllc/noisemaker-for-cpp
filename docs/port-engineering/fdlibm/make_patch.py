import difflib, pathlib

FD = pathlib.Path("docs/port-engineering/fdlibm")
OUT = []

def add_new_file(repo_path, content_path):
    content = (FD / content_path).read_text()
    lines = content.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    n = len(lines)
    OUT.append(f"diff --git a/{repo_path} b/{repo_path}\n")
    OUT.append("new file mode 100644\n")
    OUT.append("--- /dev/null\n")
    OUT.append(f"+++ b/{repo_path}\n")
    OUT.append(f"@@ -0,0 +1,{n} @@\n")
    for l in lines:
        OUT.append("+" + l)

def add_modified_file(repo_path, old_path, new_path):
    old = (FD / old_path).read_text().splitlines(keepends=True)
    new = (FD / new_path).read_text().splitlines(keepends=True)
    diff = list(difflib.unified_diff(old, new, fromfile=f"a/{repo_path}", tofile=f"b/{repo_path}", lineterm="\n", n=3))
    OUT.append(f"diff --git a/{repo_path} b/{repo_path}\n")
    OUT.extend(diff)

add_new_file("include/noisemaker/fdlibm.hpp", "fdlibm_project.hpp")
add_new_file("src/fdlibm.cpp", "fdlibm_project.cpp")
add_modified_file("CMakeLists.txt", "cmakelists_before.txt", "cmakelists_after.txt")
add_modified_file("include/noisemaker/glsl_runtime.hpp", "glsl_runtime_before.hpp", "glsl_runtime_after.hpp")

(FD / "runtime-integration.patch").write_text("".join(OUT))
print("wrote", len(OUT), "lines-of-diff-output entries")
