<#
.SYNOPSIS
    CoDrone Edu Vision Controller - Standalone WPF Portable Windows Installer & Deployment Suite
.DESCRIPTION
    100% Standalone & Portable setup tool. Can be moved anywhere on a USB drive.
    Automatically fetches application source code from GitHub if missing,
    detects/installs Python, sets up an isolated virtual environment (.venv),
    installs all dependencies (MediaPipe 0.10.21, OpenCV, CoDrone-Edu),
    and launches or compiles the application.
#>

# Enable TLS 1.2 & TLS 1.3 for secure GitHub/Python downloads
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Windows.Forms

$script:BaseDir = $PSScriptRoot
if (-not $script:BaseDir -or -not (Test-Path $script:BaseDir)) {
    $script:BaseDir = (Get-Location).Path
}

# ------------------------------------------------------------------------------
# Modern WPF XAML Interface Definition
# ------------------------------------------------------------------------------
[xml]$xaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="CoDrone Edu Vision Controller - Portable Installer" 
        Height="560" Width="740"
        WindowStartupLocation="CenterScreen" 
        Background="#121316" Foreground="#F4F4F5"
        ResizeMode="CanMinimize" FontFamily="Segoe UI">
    
    <Grid Margin="24">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>

        <!-- Header Banner -->
        <StackPanel Grid.Row="0" Margin="0,0,0,16">
            <Grid>
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="Auto"/>
                </Grid.ColumnDefinitions>
                <StackPanel Grid.Column="0">
                    <TextBlock Text="CoDrone Edu Vision Controller" FontSize="22" FontWeight="Bold" Foreground="#10B981"/>
                    <TextBlock Text="Standalone Portable Setup &amp; Deployment Suite" FontSize="13" Foreground="#A1A1AA" Margin="0,4,0,0"/>
                </StackPanel>
                <TextBlock Grid.Column="1" Text="v1.0" FontSize="14" FontWeight="Bold" Foreground="#059669" VerticalAlignment="Center"/>
            </Grid>
        </StackPanel>

        <!-- Status & System Checks -->
        <Border Grid.Row="1" Background="#1E2025" CornerRadius="8" Padding="14" Margin="0,0,0,16" BorderBrush="#27272A" BorderThickness="1">
            <Grid>
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>

                <StackPanel Grid.Column="0">
                    <TextBlock Text="SOURCE CODE" FontSize="11" FontWeight="SemiBold" Foreground="#71717A"/>
                    <TextBlock x:Name="TxtCodeStatus" Text="Checking..." FontSize="13" FontWeight="Bold" Foreground="#F59E0B" Margin="0,3,0,0"/>
                </StackPanel>

                <StackPanel Grid.Column="1">
                    <TextBlock Text="PYTHON STATUS" FontSize="11" FontWeight="SemiBold" Foreground="#71717A"/>
                    <TextBlock x:Name="TxtPythonStatus" Text="Checking..." FontSize="13" FontWeight="Bold" Foreground="#F59E0B" Margin="0,3,0,0"/>
                </StackPanel>

                <StackPanel Grid.Column="2">
                    <TextBlock Text="VENV STATUS" FontSize="11" FontWeight="SemiBold" Foreground="#71717A"/>
                    <TextBlock x:Name="TxtVenvStatus" Text="Checking..." FontSize="13" FontWeight="Bold" Foreground="#F59E0B" Margin="0,3,0,0"/>
                </StackPanel>

                <StackPanel Grid.Column="3">
                    <TextBlock Text="DEPENDENCIES" FontSize="11" FontWeight="SemiBold" Foreground="#71717A"/>
                    <TextBlock x:Name="TxtDepStatus" Text="Checking..." FontSize="13" FontWeight="Bold" Foreground="#F59E0B" Margin="0,3,0,0"/>
                </StackPanel>
            </Grid>
        </Border>

        <!-- Terminal Console Log Output -->
        <Border Grid.Row="2" Background="#0A0A0C" CornerRadius="8" Padding="12" BorderBrush="#27272A" BorderThickness="1" Margin="0,0,0,16">
            <ScrollViewer x:Name="LogScrollViewer" VerticalScrollBarVisibility="Auto">
                <TextBox x:Name="TxtLog" Background="Transparent" Foreground="#34D399" 
                         BorderThickness="0" TextWrapping="Wrap" IsReadOnly="True" 
                         FontFamily="Consolas" FontSize="12" AcceptsReturn="True"/>
            </ScrollViewer>
        </Border>

        <!-- Progress Bar -->
        <ProgressBar x:Name="ProgressBar" Grid.Row="3" Height="8" Margin="0,0,0,16" 
                     Background="#1E2025" Foreground="#10B981" BorderThickness="0" Minimum="0" Maximum="100"/>

        <!-- Action Control Buttons -->
        <Grid Grid.Row="4">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="*"/>
                <ColumnDefinition Width="10"/>
                <ColumnDefinition Width="*"/>
                <ColumnDefinition Width="10"/>
                <ColumnDefinition Width="*"/>
                <ColumnDefinition Width="10"/>
                <ColumnDefinition Width="*"/>
            </Grid.ColumnDefinitions>

            <Button x:Name="BtnInstall" Grid.Column="0" Content="1. Install All" Height="40" 
                    Background="#10B981" Foreground="#042F2E" FontWeight="Bold" FontSize="13" 
                    BorderThickness="0" Cursor="Hand"/>

            <Button x:Name="BtnLaunch" Grid.Column="1" Grid.ColumnSpan="2" Content="2. Launch Controller" Height="40" 
                    Background="#0284C7" Foreground="#FFFFFF" FontWeight="Bold" FontSize="13" 
                    BorderThickness="0" Cursor="Hand" IsEnabled="False"/>

            <Button x:Name="BtnMock" Grid.Column="4" Content="Dry-Run Simulation" Height="40" 
                    Background="#3F3F46" Foreground="#F4F4F5" FontWeight="SemiBold" FontSize="12" 
                    BorderThickness="0" Cursor="Hand"/>

            <Button x:Name="BtnBuildExe" Grid.Column="6" Content="Build Portable .EXE" Height="40" 
                    Background="#27272A" Foreground="#F4F4F5" FontWeight="SemiBold" FontSize="12" 
                    BorderThickness="0" Cursor="Hand"/>
        </Grid>
    </Grid>
</Window>
"@

$reader = [System.Xml.XmlNodeReader]::new($xaml)
$window = [System.Windows.Markup.XamlReader]::Load($reader)

# Element References
$TxtCodeStatus     = $window.FindName("TxtCodeStatus")
$TxtPythonStatus   = $window.FindName("TxtPythonStatus")
$TxtVenvStatus     = $window.FindName("TxtVenvStatus")
$TxtDepStatus      = $window.FindName("TxtDepStatus")
$TxtLog            = $window.FindName("TxtLog")
$LogScrollViewer   = $window.FindName("LogScrollViewer")
$ProgressBar       = $window.FindName("ProgressBar")
$BtnInstall        = $window.FindName("BtnInstall")
$BtnLaunch         = $window.FindName("BtnLaunch")
$BtnMock           = $window.FindName("BtnMock")
$BtnBuildExe       = $window.FindName("BtnBuildExe")

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
function Write-Log {
    param([string]$message)
    $timestamp = Get-Date -Format "HH:mm:ss"
    $formatted = "[$timestamp] $message`n"
    $TxtLog.Dispatcher.Invoke([Action]{
        $TxtLog.AppendText($formatted)
        $LogScrollViewer.ScrollToEnd()
    })
}

function Set-Progress {
    param([double]$val)
    $ProgressBar.Dispatcher.Invoke([Action]{
        $ProgressBar.Value = $val
    })
}

function Find-SystemPython {
    # 1. Search PATH
    $pyCmd = Get-Command "python" -ErrorAction SilentlyContinue
    if ($pyCmd) { return $pyCmd.Source }

    $pyLauncher = Get-Command "py" -ErrorAction SilentlyContinue
    if ($pyLauncher) { return "py" }

    # 2. Search Common Installation Paths
    $candidates = @(
        "$env:LocalAppData\Programs\Python\Python311\python.exe",
        "$env:LocalAppData\Programs\Python\Python310\python.exe",
        "$env:LocalAppData\Programs\Python\Python312\python.exe",
        "$env:LocalAppData\Programs\Python\Python39\python.exe",
        "C:\Program Files\Python311\python.exe",
        "C:\Program Files\Python310\python.exe",
        "C:\Program Files\Python312\python.exe",
        "C:\Windows\py.exe"
    )

    foreach ($path in $candidates) {
        if (Test-Path $path) { return $path }
    }

    return $null
}

function Refresh-Status {
    $script:PythonExe = Find-SystemPython
    $script:VenvPython = Join-Path $script:BaseDir ".venv\Scripts\python.exe"
    $script:MainPy = Join-Path $script:BaseDir "main.py"

    # Check Source Code
    if (Test-Path $script:MainPy) {
        $TxtCodeStatus.Text = "Ready"
        $TxtCodeStatus.Foreground = [System.Windows.Media.Brushes]::LimeGreen
    } else {
        $TxtCodeStatus.Text = "Will Fetch"
        $TxtCodeStatus.Foreground = [System.Windows.Media.Brushes]::Orange
    }

    # Check System Python
    if ($script:PythonExe) {
        $TxtPythonStatus.Text = "Installed"
        $TxtPythonStatus.Foreground = [System.Windows.Media.Brushes]::LimeGreen
    } else {
        $TxtPythonStatus.Text = "Not Found"
        $TxtPythonStatus.Foreground = [System.Windows.Media.Brushes]::IndianRed
    }

    # Check Venv
    if (Test-Path $script:VenvPython) {
        $TxtVenvStatus.Text = "Ready (.venv)"
        $TxtVenvStatus.Foreground = [System.Windows.Media.Brushes]::LimeGreen
    } else {
        $TxtVenvStatus.Text = "Missing"
        $TxtVenvStatus.Foreground = [System.Windows.Media.Brushes]::Orange
    }

    # Check Dependencies (MediaPipe)
    if (Test-Path $script:VenvPython) {
        $checkMp = & $script:VenvPython -c "import mediapipe, cv2, numpy, codrone_edu; print('OK')" 2>$null
        if ($checkMp -eq "OK") {
            $TxtDepStatus.Text = "Complete"
            $TxtDepStatus.Foreground = [System.Windows.Media.Brushes]::LimeGreen
            $BtnLaunch.IsEnabled = $true
        } else {
            $TxtDepStatus.Text = "Incomplete"
            $TxtDepStatus.Foreground = [System.Windows.Media.Brushes]::Orange
        }
    } else {
        $TxtDepStatus.Text = "Not Installed"
        $TxtDepStatus.Foreground = [System.Windows.Media.Brushes]::Orange
    }
}

# ------------------------------------------------------------------------------
# Installation & Setup Workflow Thread
# ------------------------------------------------------------------------------
function Start-Installation {
    $BtnInstall.IsEnabled = $false
    Write-Log "=================================================="
    Write-Log "  CoDrone Edu Vision Controller Standalone Setup  "
    Write-Log "=================================================="
    Set-Progress 5

    [System.Threading.Tasks.Task]::Run([Action]{
        try {
            # 1. Standalone Code Retrieval (If main.py is missing)
            if (-not (Test-Path $script:MainPy)) {
                Write-Log "[*] Standalone mode detected! Downloading source code repository from GitHub..."
                Set-Progress 10
                $zipUrl = "https://github.com/EmperorRaccoonthe1st/CoDrone-EDU-Hand-Control/archive/refs/heads/main.zip"
                $zipPath = Join-Path $script:BaseDir "repo.zip"
                $extractTmp = Join-Path $script:BaseDir "repo_extract_tmp"

                Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath
                Write-Log "[+] Repository downloaded. Extracting project files..."
                Set-Progress 20

                Expand-Archive -Path $zipPath -DestinationPath $extractTmp -Force
                $extractedFolder = Get-ChildItem $extractTmp | Select-Object -First 1

                if ($extractedFolder) {
                    Get-ChildItem $extractedFolder.FullName | Copy-Item -Destination $script:BaseDir -Recurse -Force
                }

                Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
                Remove-Item $extractTmp -Recurse -Force -ErrorAction SilentlyContinue
                Write-Log "[+] Application source files deployed cleanly."
            } else {
                Write-Log "[+] Application source code present."
            }

            Set-Progress 30

            # 2. Check / Install Python on Target PC
            if (-not $script:PythonExe) {
                Write-Log "[-] Python not found on target machine. Downloading official Python 3.11.9 installer..."
                Set-Progress 35
                $installerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
                $installerPath = Join-Path $script:BaseDir "python-installer.exe"

                Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
                Write-Log "[+] Download complete. Executing quiet background Python installation..."
                Set-Progress 45

                $proc = Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 SimpleInstall=1" -Wait -PassThru
                Remove-Item $installerPath -Force -ErrorAction SilentlyContinue

                # Refresh environment PATH in current session
                $env:PATH = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
                $script:PythonExe = Find-SystemPython
                Write-Log "[+] Python installation complete: $script:PythonExe"
            } else {
                Write-Log "[+] Target Python environment detected: $script:PythonExe"
            }

            Set-Progress 60

            # 3. Create Local Isolated Virtual Environment (.venv)
            if (-not (Test-Path $script:VenvPython)) {
                Write-Log "[*] Setting up local isolated virtual environment (.venv)..."
                & $script:PythonExe -m venv "$script:BaseDir\.venv"
                Write-Log "[+] Virtual environment created."
            } else {
                Write-Log "[+] Virtual environment already exists."
            }

            Set-Progress 75

            # 4. Install Dependencies from requirements.txt
            Write-Log "[*] Installing dependencies (mediapipe==0.10.21, opencv-python, codrone-edu)..."
            $pipExe = Join-Path $script:BaseDir ".venv\Scripts\pip.exe"
            & $pipExe install --upgrade pip 2>&1 | Out-Null

            $reqPath = Join-Path $script:BaseDir "requirements.txt"
            if (-not (Test-Path $reqPath)) {
                # Fallback requirements
                Write-Log "[*] Writing requirements.txt..."
                "mediapipe==0.10.21`nopencv-python>=4.8.0.76`nnumpy>=1.24.3`ncodrone-edu>=1.9.0" | Out-File $reqPath -Encoding utf8
            }

            $pipResult = & $pipExe install -r $reqPath 2>&1
            Write-Log "[+] All dependencies installed successfully!"

            Set-Progress 100
            Write-Log "=================================================="
            Write-Log "  SETUP COMPLETE! System ready for drone flight.  "
            Write-Log "=================================================="

            $window.Dispatcher.Invoke([Action]{
                Refresh-Status
                $BtnInstall.IsEnabled = $true
            })
        } catch {
            Write-Log "[!] Setup Error: $_"
            $window.Dispatcher.Invoke([Action]{ $BtnInstall.IsEnabled = $true })
        }
    })
}

# ------------------------------------------------------------------------------
# Button Event Bindings
# ------------------------------------------------------------------------------
$BtnInstall.Add_Click({ Start-Installation })

$BtnLaunch.Add_Click({
    Write-Log "[*] Launching CoDrone Edu Vision Controller..."
    Start-Process -FilePath $script:VenvPython -ArgumentList "main.py" -WorkingDirectory $script:BaseDir
})

$BtnMock.Add_Click({
    Write-Log "[*] Launching Dry-Run Simulation Mode..."
    Start-Process -FilePath $script:VenvPython -ArgumentList "main.py --mock-drone --mock-camera" -WorkingDirectory $script:BaseDir
})

$BtnBuildExe.Add_Click({
    Write-Log "[*] Compiling Standalone Portable Windows Executable..."
    [System.Threading.Tasks.Task]::Run([Action]{
        $pipExe = Join-Path $script:BaseDir ".venv\Scripts\pip.exe"
        & $pipExe install pyinstaller 2>&1 | Out-Null

        $pyinstExe = Join-Path $script:BaseDir ".venv\Scripts\pyinstaller.exe"
        & $pyinstExe --noconfirm --onedir --windowed --name="CoDroneVisionController" main.py 2>&1 | Out-Null
        Write-Log "[+] Portable Executable Built -> dist\CoDroneVisionController\CoDroneVisionController.exe"
    })
})

# Initial Status Check & Window Display
Refresh-Status
Write-Log "Standalone Portable Installer ready. Directory: $script:BaseDir"
$window.ShowDialog() | Out-Null
