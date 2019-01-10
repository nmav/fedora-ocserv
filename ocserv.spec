%global _hardened_build 1

%if 0%{?fedora} || 0%{?rhel} >= 7
%define use_systemd 1
%define have_gpgv2 1
%else
%define use_systemd 0
%define have_gpgv2 0
%endif

%if 0%{?fedora} >= 28 || 0%{?rhel} > 7
%define use_libwrap 0
%else
%define use_libwrap 1
%endif

%define use_local_protobuf 0

Name:		ocserv
Version:	0.11.8
Release:	1%{?dist}
Summary:	OpenConnect SSL VPN server

# For a breakdown of the licensing, see PACKAGE-LICENSING 
# To simplify licenses LGPLv2+ files have been promoted to GPLv2+.
License:	GPLv2+ and BSD and MIT and CC0
URL:		http://www.infradead.org/ocserv/
Source0:	ftp://ftp.infradead.org/pub/ocserv/%{name}-%{version}.tar.xz
Source1:	ftp://ftp.infradead.org/pub/ocserv/%{name}-%{version}.tar.xz.sig
Source2:	gpgkey-1F42418905D8206AA754CCDC29EE58B996865171.gpg
Source3:	ocserv.conf
Source4:	ocserv.service
Source5:	ocserv-pamd.conf
Source6:	PACKAGE-LICENSING
Source8:	ocserv-genkey
Source9:	ocserv-script
Source10:	gpgkey-56EE7FA9E8173B19FE86268D763712747F343FA7.gpg
Source11:	ocserv.init

# Taken from upstream:
# http://git.infradead.org/ocserv.git/commitdiff/7d70006a2dbddf783213f1856374bacc74217e09

BuildRequires:	gcc
%if 0%{?rhel} && 0%{?rhel} <= 6
BuildRequires:	gnutls30-devel
%else
BuildRequires:	gnutls-devel
%endif
BuildRequires:	pam-devel
BuildRequires:	iproute

%if (0%{?use_local_protobuf} == 0)
BuildRequires:	protobuf-c-devel
%endif

BuildRequires:	libnl3-devel
BuildRequires:	krb5-devel
BuildRequires:	libtasn1-devel
BuildRequires:	gperf
BuildRequires:	pcllib-devel
BuildRequires:	libtalloc-devel
BuildRequires:	libev-devel
BuildRequires:	http-parser-devel
%if %{use_libwrap}
BuildRequires:	tcp_wrappers-devel
%endif
BuildRequires:	automake, autoconf
BuildRequires:	radcli-devel
BuildRequires:	lz4-devel
BuildRequires:	readline-devel
BuildRequires:	GeoIP-devel

%if %{use_systemd}
BuildRequires:	systemd
BuildRequires:	systemd-devel
BuildRequires:	liboath-devel
BuildRequires:	uid_wrapper
BuildRequires:	socket_wrapper
BuildRequires:	gnupg2

%if 0%{?rhel} && 0%{?rhel} >= 7
%ifarch x86_64 %{ix86}
BuildRequires:	libseccomp-devel
%endif
%else
%ifarch x86_64 %{ix86} %{arm} aarch64
BuildRequires:	libseccomp-devel
%endif
%endif

%endif #use systemd

# no rubygem in epel7
%if 0%{?fedora} || 0%{?rhel} > 7
BuildRequires:	rubygem(ronn)
%endif

Requires:		gnutls-utils
Requires:		iproute
Requires:		pam
Requires(pre):		shadow-utils
%if %{use_systemd}
Requires(post):		systemd
Requires(preun):	systemd
Requires(postun):	systemd
%endif

#gnulib is bundled. See https://fedorahosted.org/fpc/ticket/174
Provides:		bundled(gnulib)
#CCAN is bundled. See https://fedorahosted.org/fpc/ticket/364
Provides:		bundled(bobjenkins-hash) bundled(ccan-container_of) 
Provides:		bundled(ccan-htable) bundled(ccan-list)
Provides:		bundled(ccan-check_type) bundled(ccan-build_assert)

%description
OpenConnect server (ocserv) is an SSL VPN server. Its purpose is to be a 
secure, small, fast and configurable VPN server. It implements the OpenConnect 
SSL VPN protocol, and has also (currently experimental) compatibility with 
clients using the AnyConnect SSL VPN protocol. The OpenConnect VPN protocol 
uses the standard IETF security protocols such as TLS 1.2, and Datagram TLS 
to provide the secure VPN service. 

%prep
%if %{have_gpgv2}
gpgv2 --keyring %{SOURCE2} %{SOURCE1} %{SOURCE0} || gpgv2 --keyring %{SOURCE10} %{SOURCE1} %{SOURCE0}
%endif

%autosetup -p1

rm -f src/http-parser/http_parser.c src/http-parser/http_parser.h
%if (0%{?use_local_protobuf} == 0)
rm -rf src/protobuf/protobuf-c/
touch src/*.proto
%endif
rm -rf src/ccan/talloc
rm -f src/pcl/*.c src/pcl/*.h
sed -i 's|/etc/ocserv.conf|/etc/ocserv/ocserv.conf|g' src/config.c
sed -i 's/run-as-group = nogroup/run-as-group = nobody/g' tests/data/*.config
# GPLv3 in headers is a gnulib bug: 
# http://lists.gnu.org/archive/html/bug-gnulib/2013-11/msg00062.html
sed -i 's/either version 3 of the License/either version 2 of the License/g' build-aux/snippet/*

%if 0%{?rhel} && 0%{?rhel} <= 6
echo "int main() { return 77; }" > tests/valid-hostname.c
%endif

%build

%if 0%{?rhel} && 0%{?rhel} <= 6
export PKG_CONFIG_LIBDIR="%{_libdir}/gnutls30/pkgconfig:%{_libdir}/pkgconfig"
export LIBGNUTLS_CFLAGS="-I/usr/include/gnutls30"
export LIBGNUTLS_LIBS="-L%{_libdir}/gnutls30/ -lgnutls"
export CFLAGS="$CFLAGS -I/usr/include/libev -I/usr/include/gnutls30"
sed -i 's/AM_PROG_AR//g' configure.ac
autoreconf -fvi
%endif

%configure \
%if %{use_systemd}
	--enable-systemd \
%else
	--disable-systemd \
%endif
%if %{use_local_protobuf}
	--without-protobuf \
%endif
%if %{use_libwrap}
	--with-libwrap
%else
	--without-libwrap
%endif

make #%{?_smp_mflags}

%pre
getent group ocserv &>/dev/null || groupadd -r ocserv
getent passwd ocserv &>/dev/null || \
	/usr/sbin/useradd -r -g ocserv -s /sbin/nologin -c ocserv \
		-d %{_localstatedir}/lib/ocserv ocserv
mkdir -p %{_sysconfdir}/pki/ocserv/public
mkdir -p -m 700 %{_sysconfdir}/pki/ocserv/private
mkdir -p %{_sysconfdir}/pki/ocserv/cacerts

%check
make check %{?_smp_mflags}

%if %{use_systemd}
%post
%systemd_post ocserv.service

%preun
%systemd_preun ocserv.service

%postun
%systemd_postun ocserv.service
%endif

%install
rm -rf %{buildroot}
cp -a %{SOURCE6} PACKAGE-LICENSING
mkdir -p %{buildroot}/%{_sysconfdir}/pam.d/
mkdir -p %{buildroot}/%{_sysconfdir}/ocserv/
install -p -m 644 %{SOURCE5} %{buildroot}/%{_sysconfdir}/pam.d/ocserv
install -p -m 644 %{SOURCE3} %{buildroot}/%{_sysconfdir}/ocserv/
mkdir -p %{buildroot}%{_localstatedir}/lib/ocserv/
install -p -m 644 doc/profile.xml %{buildroot}%{_localstatedir}/lib/ocserv/
mkdir -p %{buildroot}/%{_sbindir}
install -p -m 755 %{SOURCE8} %{buildroot}/%{_sbindir}
mkdir -p %{buildroot}/%{_bindir}
install -p -m 755 %{SOURCE9} %{buildroot}/%{_bindir}

%if 0%{?rhel}
sed -i 's|expiration_days=-1|expiration_days=9999|' %{buildroot}/%{_sbindir}/ocserv-genkey
sed -i 's|tls-priorities = "@SYSTEM"|tls-priorities = "NORMAL:%SERVER_PRECEDENCE:%COMPAT:-VERS-SSL3.0"|' %{buildroot}/%{_sysconfdir}/ocserv/ocserv.conf
%if 0%{?rhel} <= 6
sed -i 's|isolate-workers = true|isolate-workers = false|' %{buildroot}/%{_sysconfdir}/ocserv/ocserv.conf
%endif
%endif

%if %{use_systemd}
mkdir -p %{buildroot}/%{_unitdir}
install -p -m 644 %{SOURCE4} %{buildroot}/%{_unitdir}
%else
mkdir -p %{buildroot}/%{_initrddir}
install -D -m 0755 %{SOURCE11} %{buildroot}/%{_initrddir}/%{name}
%endif

%make_install

%files
%defattr(-,root,root,-)

%dir %{_localstatedir}/lib/ocserv
%dir %{_sysconfdir}/ocserv

%config(noreplace) %{_sysconfdir}/ocserv/ocserv.conf
%config(noreplace) %{_sysconfdir}/pam.d/ocserv

%doc AUTHORS ChangeLog NEWS COPYING LICENSE README.md TODO PACKAGE-LICENSING
%doc src/ccan/licenses/CC0 src/ccan/licenses/LGPL-2.1 src/ccan/licenses/BSD-MIT

%{_mandir}/man8/ocserv.8*
%{_mandir}/man8/occtl.8*
%{_mandir}/man8/ocpasswd.8*

%{_bindir}/ocpasswd
%{_bindir}/occtl
%{_bindir}/ocserv-fw
%{_bindir}/ocserv-script
%{_sbindir}/ocserv
%{_sbindir}/ocserv-genkey
%{_localstatedir}/lib/ocserv/profile.xml
%if %{use_systemd}
%{_unitdir}/ocserv.service
%else
%{_initrddir}/%{name}
%endif

%changelog
