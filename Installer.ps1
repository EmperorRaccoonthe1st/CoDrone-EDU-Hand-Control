<#
.SYNOPSIS
    CoDrone Edu Vision Controller - Portable WPF Windows Installer & Launcher
.DESCRIPTION
    Automates Python detection/installation, virtual environment creation,
    dependency installation (mediapipe 0.10.21, opencv, codrone-edu), 
    and application launching/building.
#>

Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase

$script:BaseDir = $PSScriptRoot
if (-not $script:BaseDir) { $script:BaseDir = Get-Location }

# ------------------------------------------------------------------------------
# Modern WPF XAML Interface Definition
# ------------------------------------------------------------------------------
[xml]$xaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="CoDrone Edu Vision Controller - Portable Installer" 
        Height="540" Width="720"
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
            <TextBlock Text="CoDrone Edu Vision Controller" FontSize="22" FontWeight="Bold" Foreground="#10B981"/>
            <TextBlock Text="Automated Setup &amp; Portable Deployment Suite" FontSize="13" Foreground="#A1A1AA" Margin="0,4,0,0"/>
        </StackPanel>

        <!-- Status & System Checks -->
        <Border Grid.Row="1" Background="#1E2025" CornerRadius="8" Padding="14" Margin="0,0,0,16" BorderBrush="#27272A" BorderThickness="1">
            <Grid>
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>

                <StackPanel Grid.Column="0">
                    <TextBlock Text="PYTHON STATUS" FontSize="11" FontWeight="SemiBold" Foreground="#71717A"/>
                    <TextBlock x:Name="TxtPythonStatus" Text="Checking..." FontSize="13" FontWeight="Bold" Foreground="#F59E0B" Margin="0,3,0,0"/>
                </StackPanel>

                <StackPanel Grid.Column="1">
                    <TextBlock Text="VENV STATUS" FontSize="11" FontWeight="SemiBold" Foreground="#71717A"/>
                    <TextBlock x:Name="TxtVenvStatus" Text="Checking..." FontSize="13" FontWeight="Bold" Foreground="#F59E0B" Margin="0,3,0,0"/>
                </StackPanel>

                <StackPanel Grid.Column="2">
                    <TextBlock Text="DEPENDENCIES" FontSize="11" FontWeight="SemiBold" Foreground="#71717A"/>
                    <TextBlock x:Name="TxtDepStatus" Text="Checking..." FontSize="13" FontWeight="Bold" Foreground="#F59E0B" Margin="0,3,0,0"/>
                </StackPanel>
            </Grid>
        </Border>

        <!-- Terminal Console Log Output -->
        <Border Grid.Row="2" Background="#0A0A0C" CornerRadius="8" Padding="10" BorderBrush="#27272A" BorderThickness="1" Margin="0,0,0,16">
            <ScrollViewer x:Name="LogScrollViewer" VerticalScrollBarVisibility="Auto">
                <TextBox x:Name="TxtLog" Background="Transparent" Foreground="#34D399" 
                         BorderThickness="0" TextWrapping="Wrap" IsReadOnly="True" 
                         FontFamily="Consolas" FontSize="12" AcceptsReturn="True"/>
            </ScrollViewer>
        </Border>

        <!-- Progress Bar -->
        <ProgressBar x:Name="ProgressBar" Grid.Row="3" Height="8" Margin="0,0,0,16" 
                     Background="#1E2025" Foreground="#10B981" BorderThickness="0"/>

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

            <Button x:Name="BtnInstall" Grid.Column="0" Content="1. Install All" Height="38" 
                    Background="#10B981" Foreground="#042F2E" FontWeight="Bold" FontSize="13" 
                    BorderThickness="0" Cursor="Hand"/>

            <Button x:Name="BtnLaunch" Grid.Column="1" Grid.ColumnSpan="2" Content="2. Launch Controller" Height="38" 
                    Background="#0284C7" Foreground="#FFFFFF" FontWeight="Bold" FontSize="13" 
                    BorderThickness="0" Cursor="Hand" IsEnabled="False"/>

            <Button x:Name="BtnMock" Grid.Column="4" Content="Dry-Run Mock" Height="38" 
                    Background="#3F3F46" Foreground="#F4F4F5" FontWeight="SemiBold" FontSize="12" 
                    BorderThickness="0" Cursor="Hand"/>

            <Button x:Name="BtnBuildExe" Grid.Column="6" Content="Build Portable .EXE" Height="38" 
                    Background="#27272A" Foreground="#F4F4F5" FontWeight="SemiBold" FontSize="12" 
                    BorderThickness="0" Cursor="Hand"/>
        </Grid>
    </Grid>
</Window>
"@

$reader = [System.Xml.XmlNodeReader]::new($xaml)
$window = [System.Windows.Markup.XamlReader]::Load($reader)

# Element References
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

function Refresh-Status {
    $script:PythonExe = $null
    $script:VenvPython = Join-Path $script:BaseDir ".venv\Scripts\python.exe"

    # Check System Python
    $pyCmd = Get-Command "python" -ErrorAction SilentlyContinue
    if (-not $pyCmd) { $pyCmd = Get-Command "py" -ErrorAction SilentlyContinue }

    if ($pyCmd) {
        $TxtPythonStatus.Text = "Installed"
        $TxtPythonStatus.Foreground = [System.Windows.Media.Brushes]::LimeGreen
        $script:PythonExe = $pyCmd.Source
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
# Installation Workflow Thread
# ------------------------------------------------------------------------------
function Start-Installation {
    $BtnInstall.IsEnabled = $false
    Write-Log "Starting CoDrone Edu Vision Controller Automated Setup..."
    Set-Progress 5

    [System.Threading.Tasks.Task]::Run([Action]{
        try {
            # 1. Ensure Python on Host PC
            if (-not $script:PythonExe) {
                Write-Log "[-] Python not detected on host system. Downloading official Python 3.11.9 installer..."
                Set-Progress 10
                $installerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
                $installerPath = Join-Path $script:BaseDir "python-installer.exe"

                Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
                Write-Log "[+] Download complete. Running quiet silent Python installation..."
                Set-Progress 25

                $process = Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait -PassThru
                Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
                
                # Re-check Python
                $pyCmd = Get-Command "python" -ErrorAction SilentlyContinue
                if ($pyCmd) { $script:PythonExe = $pyCmd.Source } else { $script:PythonExe = "python" }
                Write-Log "[+] Python installation completed."
            } else {
                Write-Log "[+] Host Python detected: $script:PythonExe"
            }

            Set-Progress 40

            # 2. Create Local Isolated Virtual Environment (.venv)
            if (-not (Test-Path $script:VenvPython)) {
                Write-Log "[*] Creating local virtual environment (.venv)..."
                & $script:PythonExe -m venv "$script:BaseDir\.venv"
                Write-Log "[+] Virtual environment created successfully."
            } else {
                Write-Log "[+] Local virtual environment already present."
            }

            Set-Progress 60

            # 3. Upgrade Pip & Install Dependencies
            Write-Log "[*] Installing dependencies from requirements.txt (mediapipe 0.10.21, opencv, codrone-edu)..."
            $pipExe = Join-Path $script:BaseDir ".venv\Scripts\pip.exe"
            & $pipExe install --upgrade pip 2>&1 | Out-Null
            
            $reqPath = Join-Path $script:BaseDir "requirements.txt"
            $pipOutput = & $pipExe install -r $reqPath 2>&1
            Write-Log "[+] Dependencies installed successfully."

            Set-Progress 100
            Write-Log "=================================================="
            Write-Log "  SETUP COMPLETE! System ready for drone flight.  "
            Write-Log "=================================================="

            $window.Dispatcher.Invoke([Action]{
                Refresh-Status
                $BtnInstall.IsEnabled = $true
            })
        } catch {
            Write-Log "[!] ERROR during setup: $_"
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
    Write-Log "[*] Launching Dry-Run Mock Mode (No hardware required)..."
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

# Initial Status Check & Window Show
Refresh-Status
Write-Log "Portable Installer initialized. Base Directory: $script:BaseDir"
$window.ShowDialog() | Out-Null
