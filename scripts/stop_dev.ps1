$ports = @(8000, 5173)

foreach ($port in $ports) {
  $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
  foreach ($connection in $connections) {
    if ($connection.OwningProcess) {
      Write-Host "Stopping process $($connection.OwningProcess) on port $port"
      Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
    }
  }
}

Write-Host "Stopped local dev services."
