<#
.SYNOPSIS
    CoDrone Edu Vision Controller - Standalone Modern Dark-Mode Installer Suite
.DESCRIPTION
    100% Self-contained & Portable. Features immersive Windows DWM dark mode,
    non-blocking background execution, comprehensive file logging, automatic
    source code extraction, non-admin Python setup, and dependency management.
#>

# Enforce TLS 1.2 & TLS 1.3 for secure downloads
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
$ProgressPreference = 'SilentlyContinue'

Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase

# Native DWM Import for Windows 10/11 Dark Mode Title Bar
try {
    Add-Type -TypeDefinition @"
    using System;
    using System.Runtime.InteropServices;
    public class DwmUtil {
        [DllImport("dwmapi.dll", PreserveSig = true)]
        public static extern int DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int attrValue, int attrSize);
    }
"@ -ErrorAction SilentlyContinue
} catch {}

$script:BaseDir = $PSScriptRoot
if (-not $script:BaseDir -or -not (Test-Path $script:BaseDir)) {
    $script:BaseDir = (Get-Location).Path
}

$script:LogFilePath = Join-Path $script:BaseDir "installer_debug.log"

# ------------------------------------------------------------------------------
# Modern Pure Dark Mode WPF XAML Definition
# ------------------------------------------------------------------------------
[xml]$xaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="CoDrone Edu Vision Controller - Portable Installer" 
        Height="580" Width="760"
        WindowStartupLocation="CenterScreen" 
        Background="#0F0F11" Foreground="#F4F4F5"
        ResizeMode="CanMinimize" FontFamily="Segoe UI">

    <Window.Resources>
        <!-- Custom Pure Dark Button Template -->
        <Style TargetType="Button">
            <Setter Property="Background" Value="#1E2025"/>
            <Setter Property="Foreground" Value="#F4F4F5"/>
            <Setter Property="BorderBrush" Value="#27272A"/>
            <Setter Property="BorderThickness" Value="1"/>
            <Setter Property="Padding" Value="10,6"/>
            <Setter Property="FontSize" Value="12"/>
            <Setter Property="FontWeight" Value="SemiBold"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border x:Name="border" 
                                Background="{TemplateBinding Background}" 
                                BorderBrush="{TemplateBinding BorderBrush}" 
                                BorderThickness="{TemplateBinding BorderThickness}" 
                                CornerRadius="6" 
                                SnapsToDevicePixels="True">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter TargetName="border" Property="Background" Value="#27272A"/>
                                <Setter TargetName="border" Property="BorderBrush" Value="#3F3F46"/>
                            </Trigger>
                            <Trigger Property="IsPressed" Value="True">
                                <Setter TargetName="border" Property="Background" Value="#18181B"/>
                            </Trigger>
                            <Trigger Property="IsEnabled" Value="False">
                                <Setter TargetName="border" Property="Background" Value="#141417"/>
                                <Setter Property="Foreground" Value="#52525B"/>
                                <Setter TargetName="border" Property="BorderBrush" Value="#18181B"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>
    </Window.Resources>
    
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
                    <TextBlock Text="Automated Setup &amp; Deployment Engine" FontSize="13" Foreground="#A1A1AA" Margin="0,4,0,0"/>
                </StackPanel>
                <TextBlock Grid.Column="1" Text="v1.0 PORTABLE" FontSize="13" FontWeight="Bold" Foreground="#059669" VerticalAlignment="Center"/>
            </Grid>
        </StackPanel>

        <!-- Status Grid -->
        <Border Grid.Row="1" Background="#18181B" CornerRadius="8" Padding="14" Margin="0,0,0,16" BorderBrush="#27272A" BorderThickness="1">
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
                    <TextBlock Text="PYTHON" FontSize="11" FontWeight="SemiBold" Foreground="#71717A"/>
                    <TextBlock x:Name="TxtPythonStatus" Text="Checking..." FontSize="13" FontWeight="Bold" Foreground="#F59E0B" Margin="0,3,0,0"/>
                </StackPanel>

                <StackPanel Grid.Column="2">
                    <TextBlock Text="VENV ENVIRONMENT" FontSize="11" FontWeight="SemiBold" Foreground="#71717A"/>
                    <TextBlock x:Name="TxtVenvStatus" Text="Checking..." FontSize="13" FontWeight="Bold" Foreground="#F59E0B" Margin="0,3,0,0"/>
                </StackPanel>

                <StackPanel Grid.Column="3">
                    <TextBlock Text="DEPENDENCIES" FontSize="11" FontWeight="SemiBold" Foreground="#71717A"/>
                    <TextBlock x:Name="TxtDepStatus" Text="Checking..." FontSize="13" FontWeight="Bold" Foreground="#F59E0B" Margin="0,3,0,0"/>
                </StackPanel>
            </Grid>
        </Border>

        <!-- Dark Terminal Output Box -->
        <Border Grid.Row="2" Background="#09090B" CornerRadius="8" Padding="12" BorderBrush="#27272A" BorderThickness="1" Margin="0,0,0,16">
            <ScrollViewer x:Name="LogScrollViewer" VerticalScrollBarVisibility="Auto">
                <TextBox x:Name="TxtLog" Background="Transparent" Foreground="#34D399" 
                         BorderThickness="0" TextWrapping="Wrap" IsReadOnly="True" 
                         FontFamily="Consolas" FontSize="12" AcceptsReturn="True"/>
            </ScrollViewer>
        </Border>

        <!-- Progress Bar -->
        <ProgressBar x:Name="ProgressBar" Grid.Row="3" Height="6" Margin="0,0,0,16" 
                     Background="#18181B" Foreground="#10B981" BorderThickness="0" Minimum="0" Maximum="100"/>

        <!-- Action Control Buttons -->
        <Grid Grid.Row="4">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="1.4*"/>
                <ColumnDefinition Width="10"/>
                <ColumnDefinition Width="1.6*"/>
                <ColumnDefinition Width="10"/>
                <ColumnDefinition Width="1.2*"/>
                <ColumnDefinition Width="10"/>
                <ColumnDefinition Width="1.2*"/>
            </Grid.ColumnDefinitions>

            <Button x:Name="BtnInstall" Grid.Column="0" Content="1. Install All" Height="40" 
                    Background="#10B981" Foreground="#042F2E" FontWeight="Bold" FontSize="13" BorderThickness="0"/>

            <Button x:Name="BtnLaunch" Grid.Column="2" Content="2. Launch Controller" Height="40" 
                    Background="#0284C7" Foreground="#FFFFFF" FontWeight="Bold" FontSize="13" BorderThickness="0" IsEnabled="False"/>

            <Button x:Name="BtnMock" Grid.Column="4" Content="Dry-Run Test" Height="40" 
                    Background="#27272A" Foreground="#F4F4F5"/>

            <Button x:Name="BtnBuildExe" Grid.Column="6" Content="Build Exe" Height="40" 
                    Background="#27272A" Foreground="#F4F4F5"/>
        </Grid>
    </Grid>
</Window>
"@

$reader = [System.Xml.XmlNodeReader]::new($xaml)
$window = [System.Windows.Markup.XamlReader]::Load($reader)

# Apply Immersive Dark Mode to Window Title Bar on Windows 10/11
$window.Add_SourceInitialized({
    try {
        $hwnd = (New-Object System.Windows.Interop.WindowInteropHelper($window)).Handle
        $darkModeAttr = 20 # DWMWA_USE_IMMERSIVE_DARK_MODE
        $trueVal = 1
        [DwmUtil]::DwmSetWindowAttribute($hwnd, $darkModeAttr, [ref]$trueVal, [System.Runtime.InteropServices.Marshal]::SizeOf([type][int]))
    } catch {}
})

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
# Robust Logging & Diagnostics System
# ------------------------------------------------------------------------------
function Write-Log {
    param([string]$message)
    $timestamp = Get-Date -Format "HH:mm:ss"
    $formatted = "[$timestamp] $message`n"
    
    # Write to UI Terminal Box
    $TxtLog.Dispatcher.Invoke([Action]{
        $TxtLog.AppendText($formatted)
        $LogScrollViewer.ScrollToEnd()
    })

    # Append to Disk Log File for Debugging
    try {
        Add-Content -Path $script:LogFilePath -Value "[$timestamp] $message" -ErrorAction SilentlyContinue
    } catch {}
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

    # 2. Search Local User AppData & System Folders
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

    # Check Python
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

    # Check Dependencies (MediaPipe & CoDrone)
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
# Installation Workflow Thread (Non-Blocking Task)
# ------------------------------------------------------------------------------
function Start-Installation {
    $BtnInstall.IsEnabled = $false
    Write-Log "=================================================="
    Write-Log "  CoDrone Edu Vision Controller Installation Log  "
    Write-Log "=================================================="
    Write-Log "Target Installation Directory: $script:BaseDir"
    Write-Log "OS Architecture: $([Environment]::Is64BitOperatingSystem ? '64-bit' : '32-bit')"
    Write-Log "PowerShell Version: $($PSVersionTable.PSVersion)"
    Set-Progress 5

    [System.Threading.Tasks.Task]::Run([Action]{
        try {
            # 1. Source Code Retrieval (Standalone Mode)
            if (-not (Test-Path $script:MainPy)) {
                Write-Log "[1/4] Standalone mode detected! Downloading source code repository from GitHub..."
                Set-Progress 10
                $zipUrl = "https://github.com/EmperorRaccoonthe1st/CoDrone-EDU-Hand-Control/archive/refs/heads/main.zip"
                $zipPath = Join-Path $script:BaseDir "repo.zip"
                $extractTmp = Join-Path $script:BaseDir "repo_extract_tmp"

                $wc = New-Object System.Net.WebClient
                $wc.DownloadFile($zipUrl, $zipPath)
                Write-Log "[+] Repository archive downloaded successfully ($( (Get-Item $zipPath).Length ) bytes)."
                Set-Progress 20

                Expand-Archive -Path $zipPath -DestinationPath $extractTmp -Force
                $extractedFolder = Get-ChildItem $extractTmp | Select-Object -First 1

                if ($extractedFolder) {
                    Get-ChildItem $extractedFolder.FullName | Copy-Item -Destination $script:BaseDir -Recurse -Force
                }

                Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
                Remove-Item $extractTmp -Recurse -Force -ErrorAction SilentlyContinue
                Write-Log "[+] Application files deployed cleanly."
            } else {
                Write-Log "[1/4] Application source files present."
            }

            Set-Progress 30

            # 2. Check / Install Non-Admin Python
            if (-not $script:PythonExe) {
                Write-Log "[2/4] Python not detected. Downloading official Python 3.11.9 64-bit installer..."
                Set-Progress 35
                $installerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
                $installerPath = Join-Path $script:BaseDir "python-installer.exe"

                $wc = New-Object System.Net.WebClient
                $wc.DownloadFile($installerUrl, $installerPath)
                Write-Log "[+] Python installer downloaded ($( (Get-Item $installerPath).Length ) bytes)."
                Write-Log "[*] Executing silent user-level Python installation..."
                Set-Progress 45

                # Silent non-admin install
                $procInfo = New-Object System.Diagnostics.ProcessStartInfo
                $procInfo.FileName = $installerPath
                $procInfo.Arguments = "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1 SimpleInstall=1"
                $procInfo.UseShellExecute = $false
                $procInfo.RedirectStandardOutput = $true
                $procInfo.RedirectStandardError = $true

                $proc = [System.Diagnostics.Process]::Start($procInfo)
                $proc.WaitForExit()
                
                Write-Log "[+] Python installer finished with exit code: $($proc.ExitCode)"
                Remove-Item $installerPath -Force -ErrorAction SilentlyContinue

                # Refresh environment PATH in current session
                $env:PATH = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
                $script:PythonExe = Find-SystemPython
                Write-Log "[+] Detected Python executable: $script:PythonExe"
            } else {
                Write-Log "[2/4] Host Python environment detected: $script:PythonExe"
            }

            Set-Progress 60

            # 3. Create Local Virtual Environment (.venv)
            if (-not (Test-Path $script:VenvPython)) {
                Write-Log "[3/4] Creating local virtual environment (.venv)..."
                
                $pInfo = New-Object System.Diagnostics.ProcessStartInfo
                $pInfo.FileName = $script:PythonExe
                $pInfo.Arguments = "-m venv `"$script:BaseDir\.venv`""
                $pInfo.UseShellExecute = $false
                $pInfo.RedirectStandardOutput = $true
                $pInfo.RedirectStandardError = $true

                $p = [System.Diagnostics.Process]::Start($pInfo)
                $pStdOut = $p.StandardOutput.ReadToEnd()
                $pStdErr = $p.StandardError.ReadToEnd()
                $p.WaitForExit()

                if ($p.ExitCode -eq 0) {
                    Write-Log "[+] Virtual environment created at $script:BaseDir\.venv"
                } else {
                    Write-Log "[!] Virtual environment creation warning: $pStdErr"
                }
            } else {
                Write-Log "[3/4] Virtual environment (.venv) already present."
            }

            Set-Progress 75

            # 4. Install Dependencies from requirements.txt
            Write-Log "[4/4] Installing dependencies (mediapipe==0.10.21, opencv-python, codrone-edu)..."
            $pipExe = Join-Path $script:BaseDir ".venv\Scripts\pip.exe"
            $reqPath = Join-Path $script:BaseDir "requirements.txt"

            if (-not (Test-Path $reqPath)) {
                "mediapipe==0.10.21`nopencv-python>=4.8.0.76`nnumpy>=1.24.3`ncodrone-edu>=1.9.0" | Out-File $reqPath -Encoding utf8
            }

            $pipInfo = New-Object System.Diagnostics.ProcessStartInfo
            $pipInfo.FileName = $pipExe
            $pipInfo.Arguments = "install -r `"$reqPath`""
            $pipInfo.UseShellExecute = $false
            $pipInfo.RedirectStandardOutput = $true
            $pipInfo.RedirectStandardError = $true

            $pipProc = [System.Diagnostics.Process]::Start($pipInfo)
            
            # Read stdout line by line for live progress logs
            while (-not $pipProc.HasExited) {
                $line = $pipProc.StandardOutput.ReadLine()
                if ($line) { Write-Log "    pip: $line" }
            }
            $pipErr = $pipProc.StandardError.ReadToEnd()

            if ($pipProc.ExitCode -eq 0) {
                Write-Log "[+] All dependencies installed successfully!"
            } else {
                Write-Log "[!] Pip installation warning: $pipErr"
            }

            Set-Progress 100
            Write-Log "=================================================="
            Write-Log "  SETUP COMPLETE! System ready for drone flight.  "
            Write-Log "=================================================="

            $window.Dispatcher.Invoke([Action]{
                Refresh-Status
                $BtnInstall.IsEnabled = $true
            })
        } catch {
            Write-Log "[!] CRITICAL SETUP ERROR: $_"
            Write-Log "[!] Stack Trace: $($_.ScriptStackTrace)"
            $window.Dispatcher.Invoke([Action]{ $BtnInstall.IsEnabled = $true })
        }
    })
}

# ------------------------------------------------------------------------------
# Button Event Handlers
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
    Write-Log "[*] Compiling Standalone Portable Executable..."
    [System.Threading.Tasks.Task]::Run([Action]{
        $pipExe = Join-Path $script:BaseDir ".venv\Scripts\pip.exe"
        & $pipExe install pyinstaller 2>&1 | Out-Null

        $pyinstExe = Join-Path $script:BaseDir ".venv\Scripts\pyinstaller.exe"
        & $pyinstExe --noconfirm --onedir --windowed --name="CoDroneVisionController" main.py 2>&1 | Out-Null
        Write-Log "[+] Executable Built -> dist\CoDroneVisionController\CoDroneVisionController.exe"
    })
})

# Initial Log & Window Display
"--- CoDrone Vision Controller Installer Session Started ---" | Out-File $script:LogFilePath -Encoding utf8
Refresh-Status
Write-Log "Pure Dark-Mode Installer initialized. Base Directory: $script:BaseDir"
Write-Log "Debug log writing active: $script:LogFilePath"

$window.ShowDialog() | Out-Null
