Name:		mvel
Version:	2.6.0.Final
Release:	1
Summary:	MVFLEX Expression Language
Group:		Development/Java
License:	ASL 2.0
URL:		https://github.com/mvel/mvel
Source0:	https://github.com/mvel/mvel/archive/refs/tags/mvel2-%{version}.tar.gz#/mvel-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	python
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
# Compile dependency. ASM is not shaded into this jar.
BuildRequires:	mvn(org.ow2.asm:asm)
BuildSystem:	maven
BuildOption(install):	--file-name mvel2 --link %{name}

Obsoletes:	%{name}-javadoc < %{version}-%{release}

%description
MVEL is an expression language for Java applications. 2.6.0.Final
requires Java 11. Make.Set._() was renamed to Make.Set._add() because
underscore is reserved. This package uses the system ASM jar instead of
shading it into org.mvel2.asm. Tests are skipped.

%prep
%autosetup -n mvel-mvel2-%{version}
rm -f ASM-LICENSE.txt src/test/resources/eventing-example.jar
python - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "http://maven.apache.org/POM/4.0.0"
ET.register_namespace("", NS)
ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

def q(name):
    return "{" + NS + "}" + name

def local(tag):
    return tag.rsplit("}", 1)[-1]

def children(elem, name):
    return [child for child in list(elem) if local(child.tag) == name]

def one(elem, name):
    found = children(elem, name)
    if not found:
        return None
    return found[0]

def text_of(elem, name):
    node = one(elem, name)
    if node is None or node.text is None:
        return ""
    return node.text.strip()

drop = {
    "maven-enforcer-plugin",
    "maven-source-plugin",
    "maven-shade-plugin",
    "maven-surefire-plugin",
    "maven-release-plugin",
    "maven-bundle-plugin",
    "maven-gpg-plugin",
    "maven-javadoc-plugin",
    "maven-surefire-report-plugin",
}

dummy = Path("src/main/java/org/mvel2/asm/Dummy.java")
if not dummy.is_file():
    raise SystemExit("missing shaded-asm placeholder")
dummy.unlink()
asm_dir = dummy.parent
if asm_dir.is_dir() and not any(asm_dir.iterdir()):
    asm_dir.rmdir()

java_files = list(Path("src/main/java").rglob("*.java"))
if len(java_files) != 329:
    raise SystemExit("java files " + str(len(java_files)))

tree = ET.parse("pom.xml")
root = tree.getroot()
for reporting in children(root, "reporting"):
    root.remove(reporting)
for profiles in children(root, "profiles"):
    root.remove(profiles)
props = one(root, "properties")
if props is not None:
    drop_props = {
        "wagon-webdav.version",
        "maven-enforcer-plugin.version",
        "maven-source-plugin.version",
        "maven-surefire-plugin.version",
        "maven-release-plugin.version",
        "maven-bundle-plugin.version",
        "maven-surefire-report-plugin.version",
        "maven-javadoc-plugin.version",
        "maven-gpg-plugin.version",
        "maven-shade-plugin.version",
    }
    for node in list(props):
        if local(node.tag) in drop_props:
            props.remove(node)
deps = one(root, "dependencies")
if deps is None:
    raise SystemExit("no dependencies")
saw_asm = False
for dep in list(deps):
    art = text_of(dep, "artifactId")
    if art == "junit":
        deps.remove(dep)
        continue
    if art == "asm" and text_of(dep, "groupId") == "org.ow2.asm":
        saw_asm = True
        ver = one(dep, "version")
        if ver is None:
            raise SystemExit("asm dependency has no version")
        ver.text = "9.11.1"
if not saw_asm:
    raise SystemExit("asm dependency missing")

build = one(root, "build")
if build is None:
    raise SystemExit("no build")
for node in children(build, "extensions"):
    build.remove(node)
for node in children(build, "resources"):
    build.remove(node)
plugins = one(build, "plugins")
if plugins is None:
    raise SystemExit("no plugins")
saw_compiler = False
saw_jar = False
for plugin in list(plugins):
    art = text_of(plugin, "artifactId")
    if art in drop:
        plugins.remove(plugin)
        continue
    if art == "maven-compiler-plugin":
        saw_compiler = True
        config = one(plugin, "configuration")
        if config is None:
            raise SystemExit("compiler plugin has no configuration")
        if text_of(config, "source") != "11" or text_of(config, "target") != "11":
            raise SystemExit("compiler source/target is not 11")
        if one(config, "release") is not None:
            raise SystemExit("compiler release was added")
    if art == "maven-jar-plugin":
        saw_jar = True
        for node in children(plugin, "executions"):
            plugin.remove(node)
        config = one(plugin, "configuration")
        if config is None:
            config = ET.SubElement(plugin, q("configuration"))
        else:
            for node in list(config):
                config.remove(node)
        archive = ET.SubElement(config, q("archive"))
        manifest = ET.SubElement(archive, q("manifest"))
        main = ET.SubElement(manifest, q("mainClass"))
        main.text = "org.mvel2.sh.Main"
        entries = ET.SubElement(archive, q("manifestEntries"))
        module = ET.SubElement(entries, q("Automatic-Module-Name"))
        module.text = "org.mvel2"
if not saw_compiler or not saw_jar:
    raise SystemExit("compiler or jar plugin missing")

tree.write("pom.xml", encoding="utf-8", xml_declaration=True)
pom = Path("pom.xml").read_text(encoding="utf-8")
for needle in (
    "<artifactId>asm</artifactId>",
    "<version>9.11.1</version>",
    "<source>11</source>",
    "<target>11</target>",
    "org.mvel2.sh.Main",
    "org.mvel2",
    "Automatic-Module-Name",
):
    if needle not in pom:
        raise SystemExit("pom missing " + needle)
for needle in (
    "maven-shade-plugin",
    "maven-bundle-plugin",
    "maven-enforcer-plugin",
    "<artifactId>wagon-webdav</artifactId>",
    "junit",
    "manifestFile",
    "SNAPSHOT",
    "build.properties",
    "org.mvel2.asm",
):
    if needle in pom:
        raise SystemExit("pom still contains " + needle)
if list(Path(".").rglob("pom.xml")) != [Path("pom.xml")]:
    raise SystemExit("unexpected extra pom")
if list(Path(".").rglob("*.jar")):
    raise SystemExit("prebuilt jar remains")
PY

%build -a
cat > manifest-addition <<'EOF'
Automatic-Module-Name: org.mvel2
EOF
jar ufm target/mvel2-%{version}.jar manifest-addition
java --module-path target/mvel2-%{version}.jar --describe-module org.mvel2 > module-describe.txt
# A versioned jar prints "name@version ... automatic", not "name automatic".
grep -q '^org.mvel2' module-describe.txt || { cat module-describe.txt; exit 1; }
grep -q ' automatic$' module-describe.txt || { cat module-describe.txt; exit 1; }
if grep -q 'contains org.mvel2.asm' module-describe.txt; then
	cat module-describe.txt
	exit 1
fi

%install -a
mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/mvel <<'EOF'
#!/bin/sh
exec java -cp %{_javadir}/mvel.jar:%{_javadir}/asm.jar org.mvel2.sh.Main "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/mvel

%files -f .mfiles
%{_bindir}/mvel
%doc README.md LICENSE.txt
