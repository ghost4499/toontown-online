# Window stuff
window-title Toontown
want-dev #f
load-display pandagl
win-size 800 600
fullscreen #f
require-window 0
cursor-filename ../toonmono.cur
icon-filename ../toontown.ico
tt-specific-login 1
required-login playToken
display-lists 0

fake-playToken faketoken

# Resource stuff
cull-bin gui-popup 60 unsorted
cull-bin shadow 15 fixed
cull-bin ground 14 fixed
textures-power-2 down
#vfs-mount phase_3.mf . 0
#vfs-mount phase_3.5.mf . 0
#vfs-mount phase_4.mf . 0
#vfs-mount phase_5.mf . 0
#vfs-mount phase_5.5.mf . 0
#vfs-mount phase_6.mf . 0
#vfs-mount phase_7.mf . 0
#vfs-mount phase_8.mf . 0
#vfs-mount phase_9.mf . 0
#vfs-mount phase_10.mf . 0
#vfs-mount phase_11.mf . 0
vfs-mount resources/phase_3 /phase_3
vfs-mount resources/phase_3.5 /phase_3.5
vfs-mount resources/phase_4 /phase_4
vfs-mount resources/phase_5 /phase_5
vfs-mount resources/phase_5.5 /phase_5.5
vfs-mount resources/phase_6 /phase_6
vfs-mount resources/phase_7 /phase_7
vfs-mount resources/phase_8 /phase_8
vfs-mount resources/phase_9 /phase_9
vfs-mount resources/phase_10 /phase_10
vfs-mount resources/phase_11 /phase_11
vfs-mount resources/phase_12 /phase_12
vfs-mount resources/phase_13 /phase_13
model-path /
default-model-extension .bam

# Audio stuff
audio-library-name p3fmod_audio
audio-sfx-active #t
audio-music-active #t
audio-master-sfx-volume 1
audio-master-music-volume 1

# DC Files
dc-file config/dcfiles/toon.dc
dc-file config/dcfiles/otp.dc

# Client stuff
paranoid-clock 1
lock-to-one-cpu 1
clock-mode limited
clock-frame-rate 120
prefer-parasite-buffer 0
want-render2dp 1
text-encoding utf8
direct-wtext 0
text-never-break-before ,.-:?!;
ime-aware 1
ime-hide 1
language english
dx-management 1
required-login playToken
want-fog #t
dx-use-rangebased-fog #t
aspect-ratio 1.333333
on-screen-debug-font ImpressBT.ttf
temp-hpr-fix 1
vertex-buffers 0
dx-broken-max-index 1
inactivity-timeout 180
merge-lod-bundles 0
early-event-sphere 1
accept-clock-skew 1
early-random-seed 1

# Server/Network stuff
server-version sv1.0.47.38
server-version-suffix 
collect-tcp 1
collect-tcp-interval 0.2
verify-ssl 0
ssl-cipher-list DEFAULT
http-preapproved-server-certificate-filename ttown4.online.disney.com:46667 gameserver.txt
decompressor-buffer-size 32768
extractor-buffer-size 32768
patcher-buffer-size 512000
downloader-timeout 15
downloader-timeout-retries 4
downloader-disk-write-frequency 4
downloader-byte-rate 125000
downloader-frequency 0.1
http-connect-timeout 20
http-timeout 30
contents-xml-dl-attempts 2
decompressor-step-time 0.5
extractor-step-time 0.5
compress-channels #t
ssl-cipher-list DEFAULT
extra-ssl-handshake-time 20.0
server-failover 80 443
server-type prod

# Debug stuff
chan-config-sanity-check #f
respect-prev-transform 1
notify-level-collide warning
notify-level-chan warning
notify-level-gobj warning
notify-level-loader warning
notify-timestamp #t