$path = "G:\SteamLibrary\steamapps\common\The Bard's Tale Trilogy\BepInEx\interop\Assembly-CSharp.dll"
$asm = [System.Reflection.Assembly]::LoadFrom($path)
$asm.GetTypes() | Where-Object { $_.Name -match "Local" -or $_.Name -match "Text" -or $_.Name -match "Language" -or $_.Name -match "String" } | Select-Object Name | Out-File types.txt
