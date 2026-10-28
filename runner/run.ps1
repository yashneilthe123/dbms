# SentinelX Review 2 - runs every script in .\steps against local MySQL and saves output in .\out
$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

$mysql = $null
foreach ($root in @("$env:ProgramFiles\MySQL", "${env:ProgramFiles(x86)}\MySQL", 'C:\xampp\mysql\bin')) {
  if (Test-Path $root) {
    $hit = Get-ChildItem $root -Recurse -Filter mysql.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit) { $mysql = $hit.FullName; break }
  }
}
if (-not $mysql) { $c = Get-Command mysql.exe -ErrorAction SilentlyContinue; if ($c) { $mysql = $c.Source } }
if (-not $mysql) { Write-Host 'Could not find mysql.exe. Is MySQL Server installed?' -ForegroundColor Red; Read-Host 'Press Enter to close'; exit 1 }
Write-Host "Using $mysql"

$sec = Read-Host 'Enter the MySQL root password' -AsSecureString
$rootPwd = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))

# test accounts created by the security scripts (local test users only)
$users = @{
  'divya'  = @('divya.iyer',  'Sx#Viewer2026');
  'rahul'  = @('rahul.mehta', 'Sx#Analyst2026');
  'ananya' = @('ananya.rao',  'Sx#Admin2026')
}

$zip = Join-Path $here 'steps.zip'
if (Test-Path $zip) { if (Test-Path (Join-Path $here 'steps')) { Remove-Item (Join-Path $here 'steps') -Recurse -Force }; Expand-Archive -Path $zip -DestinationPath $here -Force }

$out = Join-Path $here 'out'
New-Item -ItemType Directory -Force $out | Out-Null
Get-ChildItem $out -Filter *.txt | Remove-Item -Force
$cnf = Join-Path $env:TEMP 'sx_client.cnf'

$steps = Get-ChildItem (Join-Path $here 'steps') -Filter *.sql | Sort-Object Name
foreach ($s in $steps) {
  $user = 'root'; $pass = $rootPwd
  if ($s.BaseName -match '__as_(\w+)$') { $u = $users[$Matches[1]]; $user = $u[0]; $pass = $u[1] }
  "[client]`r`nuser=$user`r`npassword=`"$pass`"`r`n" | Set-Content -Path $cnf -Encoding ASCII
  $argList = "--defaults-extra-file=`"$cnf`" --table -vvv --force --default-character-set=utf8mb4"
  if ($s.Name -notlike '000_*') { $argList += ' --database=sentinelx' }
  $o = Join-Path $out ($s.BaseName + '.txt')
  $e = Join-Path $out ($s.BaseName + '.err.txt')
  Start-Process -FilePath $mysql -ArgumentList $argList -RedirectStandardInput $s.FullName `
    -RedirectStandardOutput $o -RedirectStandardError $e -NoNewWindow -Wait
  Write-Host ("ran {0} as {1}" -f $s.Name, $user)
}
Remove-Item $cnf -Force -ErrorAction SilentlyContinue

Write-Host ''
Write-Host "Done. Output files are in $out" -ForegroundColor Green
Read-Host 'Press Enter to close'
