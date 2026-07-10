$ErrorActionPreference = "Stop"

$gameDir = "d:\git\The Bard's Tale Trilogy for zh\from Steam"
$bepinexUrl = "https://builds.bepinex.dev/projects/bepinex_be/674/BepInEx-Unity.IL2CPP-win-x64-6.0.0-be.674%2Bf22e865.zip"

Write-Host "Downloading BepInEx Bleeding Edge..."
Invoke-WebRequest -Uri $bepinexUrl -OutFile "bepinex.zip"
Write-Host "Extracting BepInEx..."
Expand-Archive -Path "bepinex.zip" -DestinationPath $gameDir -Force
Remove-Item "bepinex.zip"

Write-Host "Done!"
