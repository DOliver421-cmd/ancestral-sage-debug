$zip = 'C:\Users\doliv\Documents\MORE Help Canter Files\wai_institute\Supervisor files\Seshats Hub.zip'
$dest = '.tmp_seshats'
if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
Expand-Archive -Force -Path $zip -DestinationPath $dest
Get-ChildItem $dest -Recurse | Select-Object FullName, Length | Select-Object -First 20 | Format-Table -AutoSize
