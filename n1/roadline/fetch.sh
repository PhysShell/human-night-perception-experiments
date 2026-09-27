#!/usr/bin/env bash
# Fetch the RoadLine LM-63 files (not committed: all rights reserved, see LUMINAIRE.md) and verify sha256.
set -euo pipefail; cd "$(dirname "$0")"; mkdir -p work
B=https://www.webtools.cooperlighting.com/Public/files/ies/instabase/STREETWORKS/ROADWAY
get() { [ -f "work/$1" ] || curl -sfL --max-time 60 -o "work/$1" "$2"; echo "$3  work/$1" | sha256sum -c --quiet && echo "OK $1"; }
get A_archeon.ies "$B/ARCH%20ARCHEON%20SMALL/7030-3000K-70CRI/AF16%20(16LED)/ARCH-AF16-50-D-U-T2R-7030.ies" 01f3de18177558ebeff243596f711ae2be1a060763b540dece1505a46584b4b9
get B_rma.ies "$B/RMA%20RMC%20SECURITY%20LIGHT/RMA15SXX22.ies" 5041092f4b4a2f828305646e90c2fb8b9c0be7724ce707249f2c8e48b34c6184
