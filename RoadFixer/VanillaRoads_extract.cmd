@echo off
setlocal enabledelayedexpansion

echo Searching for DayZ installation path...

set reg_keys=HKLM\SOFTWARE\Wow6432Node\Bohemia Interactive\Dayz HKLM\SOFTWARE\Bohemia Interactive\Dayz HKCU\SOFTWARE\valve\steam

for %%k in (%reg_keys%) do (
    for /f "tokens=2*" %%i in ('reg query "%%k" /v "main" 2^>nul ^| find /i "main"') do (
        set dayz_path=%%j
        if defined dayz_path (
            if "%%k" == "HKCU\SOFTWARE\valve\steam" (
                set dayz_path=!dayz_path!\steamapps\common\DayZ
            )
            goto found_dayz
        )
    )
)

echo DayZ installation path not found. Verify that the game is installed and try again.
pause
exit /b

:found_dayz

echo DayZ installation found at: %dayz_path%

if not exist "%dayz_path%\Addons\DZ.pbo" (
    echo "%dayz_path%\Addons\DZ.pbo" does not exist. You have the wrong game folder.
    pause
    exit /b
)

echo DayZ installation path is correct.

pause
