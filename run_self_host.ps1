<#
.SYNOPSIS
    JobAutomator AI - Script de Gestão e Execução Self-Hosted
.DESCRIPTION
    Permite autenticar no LinkedIn, testar o preenchimento de formulários e rodar o orquestrador reativo localmente.
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Clear-Host

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   JobAutomator AI - Painel de Execução Self-Hosted       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Função para localizar ou configurar o JAVA_HOME automaticamente
function Resolve-JavaHome {
    if ($env:JAVA_HOME -and (Test-Path "$env:JAVA_HOME\bin\java.exe")) {
        return $env:JAVA_HOME
    }

    # Candidatos padrão de instalação do JDK no Windows
    $candidatePaths = @(
        "C:\Program Files\Eclipse Adoptium\jdk-21*",
        "C:\Program Files\Java\jdk-21*",
        "C:\Program Files\Microsoft\jdk-21*",
        "C:\Program Files\Amazon Corretto\jdk-21*",
        "C:\Program Files\BellSoft\LibericaJDK-21*",
        "C:\Program Files\Eclipse Adoptium\jdk*",
        "C:\Program Files\Java\jdk*",
        "$env:USERPROFILE\.jdks\*",
        "$env:LOCALAPPDATA\Programs\Eclipse Adoptium\jdk-21*"
    )

    foreach ($pattern in $candidatePaths) {
        $found = Get-Item $pattern -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
        if ($found -and (Test-Path "$($found.FullName)\bin\java.exe")) {
            return $found.FullName
        }
    }

    # Tentativa de inferir a partir do comando java no PATH
    $javaCmd = Get-Command java -ErrorAction SilentlyContinue
    if ($javaCmd) {
        $binDir = Split-Path $javaCmd.Source -Parent
        $rootDir = Split-Path $binDir -Parent
        if (Test-Path "$rootDir\bin\java.exe") {
            return $rootDir
        }
    }

    return $null
}

# 1. Checagem de Ambiente Python
$PythonExe = ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python.exe"
}

Write-Host "`n[Verificação de Ambiente]" -ForegroundColor Yellow
Write-Host " -> Python Runner: $PythonExe"

# 2. Checagem de Sessão LinkedIn
if (Test-Path "sessions\linkedin_state.json") {
    Write-Host " -> Sessão LinkedIn: [OK] Encontrada em sessions\linkedin_state.json" -ForegroundColor Green
} else {
    Write-Host " -> Sessão LinkedIn: [AVISO] Nenhuma sessão ativa salva ainda." -ForegroundColor Yellow
}

# 3. Checagem de Java / JDK
$detectedJava = Resolve-JavaHome
if ($detectedJava) {
    $env:JAVA_HOME = $detectedJava
    Write-Host " -> Java (JAVA_HOME): [OK] $env:JAVA_HOME" -ForegroundColor Green
} else {
    Write-Host " -> Java (JAVA_HOME): [NÃO DETECTADO] Requer JDK 21 para a opção 3" -ForegroundColor Yellow
}

Write-Host "`nEscolha a operação desejada:" -ForegroundColor White
Write-Host " [1] Conectar no LinkedIn (Salvar Sessão Interativa - Login Único)" -ForegroundColor Green
Write-Host " [2] Testar Preenchimento de Formulário com Tela Visível (Dry-run)" -ForegroundColor Cyan
Write-Host " [3] Executar Orquestrador Principal Reativo (Java 21 / AgentScope)" -ForegroundColor Magenta
Write-Host " [4] Rodar Bateria de Testes Automatizados (Python + Java)" -ForegroundColor Blue
Write-Host " [5] Testar Conexão com Supabase e Sincronizar Sessão/Perfil" -ForegroundColor DarkCyan
Write-Host " [6] Abrir LinkedIn para Ajustar Idioma de Volta para Português" -ForegroundColor Yellow
Write-Host " [0] Sair" -ForegroundColor Gray

$choice = Read-Host "`nDigite a opção desejada (0-6)"

switch ($choice) {
    "1" {
        Write-Host "`nIniciando navegador com tela para autenticação..." -ForegroundColor Yellow
        & $PythonExe src/browsergym_service.py --login
    }
    "2" {
        $testUrl = Read-Host "`nInforme a URL da vaga no LinkedIn (ou pressione Enter para URL de teste)"
        if ([string]::IsNullOrWhiteSpace($testUrl)) {
            $testUrl = "https://www.linkedin.com/jobs/search/?keywords=Developer"
        }
        Write-Host "`nExecutando simulação de candidatura com tela visível..." -ForegroundColor Yellow
        & $PythonExe src/browsergym_service.py --apply --job-url "$testUrl" --headless "false"
    }
    "3" {
        if (-not $env:JAVA_HOME) {
            Write-Host "`n[AVISO] O JDK 21 não foi localizado no seu Windows." -ForegroundColor Red
            Write-Host "O Maven precisa da variável JAVA_HOME apontando para o JDK 21." -ForegroundColor Yellow
            Write-Host "`nPara instalar o Java 21 facilmente, execute no PowerShell (como Administrador):" -ForegroundColor Cyan
            Write-Host "  winget install EclipseAdoptium.Temurin.21.JDK" -ForegroundColor White
            Write-Host "Ou baixe o instalador oficial em: https://adoptium.net/temurin/releases/?version=21" -ForegroundColor Gray
            Write-Host "`n(Nota: Você já pode usar a Opção 2 normalmente enquanto isso, pois ela roda diretamente via Python!)`n" -ForegroundColor Green
            break
        }
        Write-Host "`nIniciando Orquestrador Reativo Java..." -ForegroundColor Yellow
        ./mvnw.cmd compile exec:java -Dexec.mainClass="com.jobautomator.Main"
    }
    "4" {
        Write-Host "`nExecutando testes Python..." -ForegroundColor Yellow
        & $PythonExe -m unittest discover tests
        if ($env:JAVA_HOME) {
            Write-Host "`nExecutando testes Java..." -ForegroundColor Yellow
            ./mvnw.cmd test
        }
    }
    "5" {
        Write-Host "`nTestando conexão com Supabase..." -ForegroundColor Yellow
        & $PythonExe src/supabase_client.py
    }
    "6" {
        Write-Host "`nAbrindo página de preferências de idioma do LinkedIn..." -ForegroundColor Yellow
        Start-Process "https://www.linkedin.com/mypreferences/d/language"
        Write-Host "Basta selecionar 'Português' no primeiro campo de idioma e salvar!`n" -ForegroundColor Green
    }
    Default {
        Write-Host "`nOperação finalizada." -ForegroundColor Gray
    }
}
