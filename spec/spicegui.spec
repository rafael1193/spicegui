Name:       spicegui
Version:    0.1
Release:    2%{?dist}
Summary:    SpiceGUI for circuit simulation

License:    GPLv3
URL:        http://rafael1193.github.io
Source0:    spicegui-%{version}.tar.gz

BuildRequires:  desktop-file-utils
BuildRequires:  python2-devel
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

BuildArch:      noarch


%description
SpiceGUI is a graphical user interface for ngspice circuit simulator. It aims
to make easier circuit simulation on GNU/Linux and integrate well with the GNOME
desktop.

%prep
%setup -q


%build
%{__python} setup.py build


%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot} --record=INSTALLED_FILES


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
* Tue Oct 28 2014 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.1-2
- Add gtk-update-icon-cache fix glib-compile-schemas

* Mon Oct 27 2014 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.1-1
- Update build system

* Wed Sep 03 2014 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.1-0
- Initial package
