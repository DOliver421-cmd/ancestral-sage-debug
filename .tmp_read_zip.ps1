Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = 'C:\Users\doliv\Documents\MORE Help Canter Files\wai_institute\Supervisor files\Seshats Hub.zip'
$entryName = 'Seshats Hub/seshat_hub.html'
$archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
$entry = $archive.GetEntry($entryName)
if ($entry -eq $null) { Write-Error "Entry not found: $entryName"; exit 1 }
$reader = New-Object System.IO.StreamReader($entry.Open())
for ($i=0; $i -lt 80 -and -not $reader.EndOfStream; $i++) { Write-Output $reader.ReadLine() }
$reader.Close()
$archive.Dispose()
