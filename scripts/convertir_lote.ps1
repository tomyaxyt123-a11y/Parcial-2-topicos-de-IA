param([string]$listaPath)
if (-not (Test-Path $listaPath)) { exit 0 }
$rutas = Get-Content $listaPath -Encoding UTF8 | Where-Object { $_.Trim() -ne "" }
if ($rutas.Count -eq 0) { exit 0 }

$ppt = New-Object -ComObject PowerPoint.Application
try {
    foreach ($archivo in $rutas) {
        $archivo = $archivo.Trim()
        if (Test-Path $archivo) {
            $pdfPath = [System.IO.Path]::ChangeExtension($archivo, "pdf")
            if (-not (Test-Path $pdfPath)) {
                $pres = $ppt.Presentations.Open((Resolve-Path $archivo).Path, 1, 0, 0)
                $pres.SaveAs($pdfPath, 32)
                $pres.Close()
            }
        }
    }
} finally {
    $ppt.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
