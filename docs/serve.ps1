# Usage: . serve.ps1
$requires = "mkdocs_material-4.4.0"
rez env $requires -- mkdocs serve
