Name:       spicegui
Version:    1.0
Release:    1
Summary:    Run circuit simulations and display the results

License:    GPLv3
URL:        http://github.com/rafael1193/spicegui
Source0:    %{name}-%{version}.tar.gz

BuildRequires:  desktop-file-utils
BuildRequires:  python3-setuptools
BuildRequires:  gettext
Requires:       python3
Requires:       python3-gobject
Requires:       python3-matplotlib
Requires:       python3-matplotlib-gtk3
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
%setup -q%{!?rel_build:n %{name}-%{version}}


%build
%{__python} setup.py build


%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot} --record=INSTALLED_FILES

if [ -e %{buildroot}/usr/share/glib-2.0/schemas/gschemas.compiled ] ; then
    rm %{buildroot}/usr/share/glib-2.0/schemas/gschemas.compiled
fi

%find_lang %{name} --all-name

for file in $RPM_BUILD_ROOT%{python_sitelib}/%{name}/{config,__init__}.py; do
   chmod a+x $file
done

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

%files -f INSTALLED_FILES -f %{name}.lang
%defattr(-,root,root)


%changelog
* Sat Jun 13 2015 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 1.0-1
- Update to 1.0

* Sat Jun 06 2015 Rafael Bailón-Ruiz <rafaelbailon at ieee dot org> - 0.3-4
- Fix rpmlint warnings

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
