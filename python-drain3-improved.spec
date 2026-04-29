Name:           python-drain3-improved
Version:        0.10.0
Release:        %autorelease
Summary:        Persistent & streaming log template miner
License:        MIT
URL:            https://pypi.org/project/drain3-improved/
Source0:        %{pypi_source drain3-improved}

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
Persistent & streaming log template miner
}

%description %_description

%package -n python3-drain3-improved
Summary:  %{summary}
Provides: drain3-improved

%description -n python3-drain3-improved %_description

%pyproject_extras_subpkg -n python3-drain3-improved kafka redis valkey

%prep
%autosetup -p1 -n drain3-improved-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files 'drain3'

%check
%pyproject_check_import -e drain3.valkey_persistence -e drain3.redis_persistence -e drain3.kafka_persistence


%files -n python3-drain3-improved -f %{pyproject_files}
%license LICENSE.txt
%doc README.md


%changelog
%autochangelog
