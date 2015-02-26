"""A script to generate ENSIME configs for Maven scala projects

ENSIME (ENhanced Scala Interaction Mode for Emacs) provides IDE-like
features in emacs for Scala. It primarily targets sbt and Maven support
is out of date.
"""
import os
import subprocess
import sys

DEFAULT_SCALA_VERSION = "2.11.5"

PROJECT_TEMPLATE = "\n".join([
    "(",
    "  :name {name}",
    "  :scala-version {scala_version}",
    "  :root-dir {root_dir}",
    "  :cache-dir {cache_dir}",
    "  :java-home {java_home}",
    "  :subprojects (",
    "{subproject_list}",
    "  )",
    ")",
])


SUBPROJECT_TEMPLATE = "\n".join([
    "    (",
    "      :name {name}",
    "      :module_name {name}",
    "      :target {target}",
    "      :test-target {test_target}",
    "      :source-roots {source_roots}",
    "      :compile-deps {compile_deps}",
    "      :runtime-deps {runtime_deps}",
    "      :test-deps {test_deps}",
    "    )",
])


def main():
    root = os.path.abspath(sys.argv[1])
    name = os.path.basename(root)
    subprojects = []
    subprojects.append(
        SUBPROJECT_TEMPLATE.format(
            name=quote(name),
            target=quote(os.path.join(root, "target", "ensime", "classes")),
            test_target=quote(os.path.join(
                root, "target", "ensime", "test-classes")),
            source_roots=mk_string_list([os.path.join(root, "src/main/scala")]),
            compile_deps=mk_string_list(
                deps("", dir=root).union(deps("compile", dir=root))),
            runtime_deps=mk_string_list(deps("runtime", dir=root)),
            test_deps=mk_string_list(deps("test", dir=root)),
        )
    )

    project = PROJECT_TEMPLATE.format(
        name=quote(name),
        scala_version=quote(DEFAULT_SCALA_VERSION),
        root_dir=quote(root),
        cache_dir=quote(os.path.join(root, ".ensime_cache")),
        java_home=quote(os.environ["JAVA_HOME"]),
        subproject_list="\n".join(subprojects)
    )
    print project


def run_process(exe):
    p = subprocess.Popen(
        exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    while True:
        retcode = p.poll() #returns None while subprocess is running
        line = p.stdout.readline()
        yield line
        if retcode is not None:
            break


def deps(scope, dir=None):
    """Returns set of dependency paths for given Maven scope."""
    dir_part = "-f {}".format(dir) if dir else ""
    cmd = "mvn {dir} dependency:build-classpath -DincludeScope={scope}".format(
        dir=dir_part, scope=scope)
    output_lines = [line.strip() for line in run_process(cmd)]
    prev_line = ""
    for line in output_lines:
        if prev_line.startswith("[INFO] Dependencies classpath:"):
            return set(line.split(":"))
        else:
            prev_line = line
    return set([])


def quote(obj):
    return "\"" + str(obj) + "\""


def mk_string_list(lst):
    return "(" + " ".join([quote(ea) for ea in lst]) + ")"


if __name__ == '__main__':
    main()


