param(
  [Parameter(Mandatory=$true)][string]$Playlist,
  [string]$Output = "./music-backup",
  [string]$Api = "http://127.0.0.1:3000",
  [ValidateSet("32k","40k","48k","56k","64k","80k","96k","112k","128k","160k","192k","224k","256k","320k")][string]$Bitrate = "128k",
  [ValidateSet("standard","higher","exhigh","lossless","hires","jyeffect","sky","dolby","jymaster")][string]$Level = "exhigh"
)
python .\netease_playlist_backup.py $Playlist --output $Output --api $Api --bitrate $Bitrate --level $Level
