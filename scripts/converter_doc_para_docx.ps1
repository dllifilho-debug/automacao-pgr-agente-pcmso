param(
    [string]$Origem = "matrizes_originais",
    [string]$Destino = "relatorios\docx_convertidos"
)

New-Item -ItemType Directory -Force -Path $Destino | Out-Null
$destino = (Resolve-Path $Destino).Path

$word = New-Object -ComObject Word.Application
$word.Visible = $true   # medido: Visible=$false trava a abertura de forma reproduzivel neste host (mesmo arquivo, mesmas opcoes, only Visible muda) - manter true
$word.DisplayAlerts = 0   # wdAlertsNone - suprime alertas gerais
$word.Options.ConfirmConversions = $false   # suprime o dialogo "Confirmar Conversao de Arquivo" ao abrir .doc nao-nativo

$convertidos = 0
$falhas = @()

try {
    Get-ChildItem (Join-Path $Origem "MATRIZ*.doc") | ForEach-Object {
        $arquivo = $_
        $saida = Join-Path $destino ($arquivo.BaseName + ".docx")
        $doc = $null
        try {
            $doc = $word.Documents.Open($arquivo.FullName, $false, $true)
            $doc.SaveAs2($saida, 16)
            Write-Host "convertido: $($arquivo.Name)"
            $convertidos++
        } catch {
            Write-Host "FALHOU: $($arquivo.Name) - $($_.Exception.Message)" -ForegroundColor Red
            $falhas += $arquivo.Name
        } finally {
            if ($doc) {
                $doc.Close($false)
            }
        }
    }
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}

Copy-Item (Join-Path $Origem "MATRIZ*.docx") $destino -ErrorAction SilentlyContinue

Write-Host "---"
Write-Host "Convertidos: $convertidos"
if ($falhas.Count -gt 0) {
    Write-Host "Falhas ($($falhas.Count)):"
    $falhas | ForEach-Object { Write-Host "  - $_" }
}
Write-Host "Total .docx em ${destino}: $((Get-ChildItem (Join-Path $destino '*.docx')).Count)"
