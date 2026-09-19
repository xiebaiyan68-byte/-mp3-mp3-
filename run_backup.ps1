param(
  [Parameter(Mandatory=$true)][string]$Playlist,
  [string]$Output = "./music-backup",
  [string]$Api = "http://127.0.0.1:3000",
  [ValidateSet("128k","96k")][string]$Bitrate = "128k",
  [ValidateSet("standard","higher","exhigh","lossless")][string]$Level = "exhigh"
)
python .\netease_playlist_backup.py $Playlist --output $Output --api $Api --bitrate $Bitrate --level $Level
