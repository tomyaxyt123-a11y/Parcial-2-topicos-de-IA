$pptxPath = Resolve-Path "Certificados.pptx"
$pdfPath = [System.IO.Path]::Combine((Resolve-Path "templates"), "plantilla_certificados.pdf")

$ppt = New-Object -ComObject PowerPoint.Application
try {
    $presentation = $ppt.Presentations.Open($pptxPath.Path, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    # 32 = ppSaveAsPDF
    $presentation.SaveAs($pdfPath, 32)
    $presentation.Close()
    Write-Output "PDF_EXPORT_OK: $pdfPath"
} catch {
    Write-Error $_
} finally {
    $ppt.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
}
