# Conditional for release and snapshot builds. Uncomment for release-builds.
#global rel_build 1

# Settings used for build from snapshots.
%{!?rel_build:%global commit		d9d2097ae3ae733a611178e765419eaae9ab75b7}
%{!?rel_build:%global commit_date	20150606}
%{!?rel_build:%global shortcommit	%(c=%{commit};echo ${c:0:7})}
%{!?rel_build:%global gitver		git%{commit_date}-%{shortcommit}}
%{!?rel_build:%global gitrel		.git%{commit_date}.%{shortcommit}}

# Proper naming for the tarball from github.
%global gittar %{name}-%{version}%{!?rel_build:-%{gitver}}.tar.gz

Name:       spicegui
Version:    0.3
Release:    3%{?gitrel}%{?dist}
Summary:    SpiceGUI for circuit simulation

License:    GPLv3
URL:        http://github.com/rafael1193/spicegui
# Sources for release-builds.
%{?rel_build:Source0:	%{url}/archive/v%{version}.tar.gz#/%{gittar}}
# Sources for snapshot-builds.
%{!?rel_build:Source0:	%{url}/archive/%{commit}.tar.gz#/%{gittar}}
#Source0:    spicegui-%{version}.tar.gz


BuildRequires:  desktop-file-utils
#BuildRequires:  python2-devel
BuildRequires:  python-setuptools
Requires:       python
Requires:       pygobject2
Requires:       python-matplotlib
Requires:       gtk3
Requires:       glib2
Requires:       gtksourceview3
Requires:       pango
Requires:       ngspice
Requires:       geda-gnetlist
Requires:       geda-gschem
Requires:       gettext

BuildArch:      noarch


%description
SpiceGUI is a graphical user interface for ngspice circuit simulator. It aims
to make easier circuit simulation on GNU/Linux and integrate well with the GNOME
desktop.

%prep
%setup -q%{!?rel_build:n %{name}-%{commit}}


%build
%{__python} setup.py build


%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot} --record=INSTALLED_FILES
rm %{buildroot}/usr/share/glib-2.0/schemas/gschemas.compiled

%check
%{__python} setup.py test
desktop-file-validate $RPM_BUILD_ROOT%{_datadir}/applications/SpiceGUI.desktop


%postun
if [ $1 -eq 0 ] ; then
  /bin/touch --no-create %{_datadir}/icons/hicolor/ &>/dev/null
  /usr/bin/gtk-update-icon-cache -f %{_datadir}/icons/hicolor/ &>/dev/null || :
fi
/usr/bin/glib-compile-schemas %{_datadir}/glib-2.0/schemas &>/dev/null || :


%posttrans
/usr/bin/gtk-update-icon-cache -f %{_datadir}/icons/hicolor &>/dev/null || :
/usr/bin/glib-compile-schemas %{_datadir}/glib-2.0/schemas &>/dev/null || :

%files -f INSTALLED_FILES
%defattr(-,root,root)


%changelog
* Sat Jun 06 2015 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.3-3
- Remove python2-devel build requirement
- Implement snapshot builds

* Sun Dec 21 2014 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.3-2
- Add gettext dependency

* Sun Dec 21 2014 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.3-1
- Update to 0.3

* Thu Nov 13 2014 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.2-4
- Include appdata file

* Thu Nov 13 2014 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.2-3
- Revert Source0

* Wed Nov 12 2014 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.2-2
- Update Source0

* Wed Nov 12 2014 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.2-1
- New SpiceGUI release

* Wed Nov 12 2014 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.1-3
- Add geda-gschem dependency

* Tue Oct 28 2014 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.1-2
- Add gtk-update-icon-cache fix glib-compile-schemas

* Mon Oct 27 2014 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.1-1
- Update build system

* Wed Sep 03 2014 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.1-0
- Initial package
