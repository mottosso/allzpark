@echo off

:: Do not affect parent shell
:: Without this, the below variables are
:: written to the parent shell
setlocal

:: Without this, resolving contexts may take seconds to minutes
if "%REZ_MEMCACHED_URI%"=="" (set REZ_MEMCACHED_URI=127.0.0.1:11211)

:: Supports Python 2.7 and Python 3.6+, along with any version of PySide, PySide2, PyQt4 and PyQt5
if "%LAUNCHAPP_REQUIRE%"=="" (set LAUNCHAPP_REQUIRE=rez python-3 PySide2)

rez env %LAUNCHAPP_REQUIRE% -- python -m launchapp2 --verbose %*
