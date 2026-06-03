$env:Path = [Environment]::GetEnvironmentVariable("Path","User") + ";" + [Environment]::GetEnvironmentVariable("Path","Machine")
Set-Location "C:\xampp\htdocs\Sistema Inteligente_Gestion de Citas Medicas\frontend"
npm run dev
