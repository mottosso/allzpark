@echo off

:: Do not affect parent shell
:: Without this, the below variables are
:: written to the parent shell
setlocal

python -m allspark %*
