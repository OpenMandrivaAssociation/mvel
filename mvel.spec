%{?_javapackages_macros:%_javapackages_macros}
%global namedreltag .Final
%global namedversion %{version}%{?namedreltag}
Name:          mvel
Version:       2.1.6
Release:       1.0%{?dist}
Summary:       MVFLEX Expression Language
License:       ASL 2.0
Url:           http://mvel.codehaus.org/
Source0:       https://github.com/mvel/mvel/archive/%{name}2-%{namedversion}.tar.gz

Source1:       %{name}-script
Patch0:        %{name}-2.1.6.Final-use-system-asm.patch
# remove tests which require internal objectweb-asm libraries
Patch1:        %{name}-2.1.6.Final-tests.patch

BuildRequires: java-devel

BuildRequires: mvn(asm:asm)
BuildRequires: mvn(asm:asm-util)
# test deps 
BuildRequires: mvn(junit:junit)
BuildRequires: mvn(com.thoughtworks.xstream:xstream)

BuildRequires: maven-local
BuildRequires: maven-plugin-bundle
BuildRequires: maven-surefire-provider-junit4
BuildRequires: maven-surefire-report-plugin

BuildArch:     noarch

%description
MVEL is a powerful expression language for Java-based applications. It
provides a plethora of features and is suited for everything from the
smallest property binding and extraction, to full blown scripts.

%package javadoc
Summary:       Javadoc for %{name}

%description javadoc
This package contains javadoc for %{name}.

%prep
%setup -q -n %{name}-%{name}2-%{namedversion}
find . -name "*.jar" -delete
find . -name "*.class" -delete
rm ASM-LICENSE.txt
%patch0 -p1
%patch1 -p1

# Uwanted
%pom_remove_plugin :maven-source-plugin
# Remove org.apache.maven.wagon:wagon-webdav:1.0-beta-2
%pom_xpath_remove "pom:project/pom:build/pom:extensions"

sed -i 's/\r//' LICENSE.txt

# fix non ASCII chars
native2ascii -encoding UTF8 src/main/java/org/mvel2/sh/ShellSession.java src/main/java/org/mvel2/sh/ShellSession.java

%build

%mvn_file :%{name}2 %{name}
# some test at random fails
%mvn_build -- -Dmaven.test.failure.ignore=true

%install
%mvn_install

mkdir -p %{buildroot}%{_bindir}
install -pm 755 %{SOURCE1} %{buildroot}%{_bindir}/%{name}

install -m 644 target/%{name}2-%{namedversion}-tests.jar %{buildroot}%{_javadir}/%{name}-tests.jar

%files -f .mfiles
%{_bindir}/%{name}
%{_javadir}/%{name}-tests.jar
%doc LICENSE.txt

%files javadoc -f .mfiles-javadoc
%doc LICENSE.txt

%changelog
* Mon Sep 16 2013 gil cattaneo <puntogil@libero.it> 2.1.6-1
- update to 2.1.6.Final

* Fri Jul 05 2013 gil cattaneo <puntogil@libero.it> 2.0.19-5
- switch to XMvn
- minor changes to adapt to current guideline

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.19-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Feb 06 2013 Java SIG <java-devel@lists.fedoraproject.org> - 2.0.19-3
- Update for https://fedoraproject.org/wiki/Fedora_19_Maven_Rebuild
- Replace maven BuildRequires with maven-local

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.19-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sat May 26 2012 gil cattaneo <puntogil@libero.it> 2.0.19-1
- initial rpm