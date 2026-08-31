Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = 'C:\Users\doliv\Documents\MORE Help Canter Files\wai_institute\Supervisor files\Seshats Hub.zip'
$archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
$archive.Entries | Select-Object FullName,Length | Format-Table -AutoSize
$archive.Dispose()
