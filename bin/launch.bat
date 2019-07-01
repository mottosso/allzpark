@echo off

:: Do not affect parent shell
:: Without this, the below variables are
:: written to the parent shell
setlocal

:: These can be overridden
if "%REZ_PACKAGES_PATH%"=="" (set REZ_PACKAGES_PATH=%USERPROFILE%\packages)

:: Without this, resolving contexts may take seconds to minutes
if "%REZ_MEMCACHED_URI%"=="" (set REZ_MEMCACHED_URI=127.0.0.1:11211)

:: Defaults to finding projects in your home directory
if "%LAUNCHAPP_ROOT%"=="" (set LAUNCHAPP_ROOT=%USERPROFILE%\projects)

python -m allspark %*
