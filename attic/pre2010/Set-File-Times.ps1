$newTime = New-Object System.DateTime(2004, 4, 4, 4, 0, 0)
Get-ChildItem | ForEach-Object { 
    $_.CreationTime = $_.LastWriteTime = $_.LastAccessTime = $newTime;
    $newTime = $newTime.AddMinutes(1);
    Get-ChildItem $_ | ForEach-Object {  $_.CreationTime = $_.LastWriteTime = $_.LastAccessTime = $newTime; $newTime = $newTime.AddMinutes(1);

    }
}
