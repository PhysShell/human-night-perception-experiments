## RETINAL TARGETS (achromatic B0-optics; trunk P_det, HDR-VDP-3 observer model)

| target (observer model X) | route | x0.1 (8.9e-06 lx) | x1 (8.9e-05 lx) | x10 (8.9e-04 lx) | x100 (8.9e-03 lx) |
|---|---|---|---|---|---|
| ISETBio wvf human, 550 nm, 6 mm, defocus 0 | donor optics, evaluator OFF, 73 px/deg | 0.275 | 0.088 | 0.025 | 0.007 |
| HDR-VDP-3 eye MTF | donor optics, evaluator OFF, 73 px/deg | 0.027 | 0.005 | 0.000 | 0.000 |
| CIE 135/1 (Vos-van den Berg 1999), age 24, 4x grid | donor optics, evaluator OFF, 73 px/deg | 0.268 | 0.123 | 0.038 | 0.004 |
| no optics (physical stimulus) | donor optics, evaluator OFF, 73 px/deg | 0.552 | 0.514 | 0.475 | 0.438 |
| HDR-VDP-3 eye MTF | evaluator optics on the physical stimulus, 146 px/deg | 0.051 | 0.009 | 0.000 | 0.000 |
| CIE 135/1 (Vos-van den Berg 1999), age 24, 4x grid | evaluator optics on the physical stimulus, 146 px/deg | 0.285 | 0.132 | 0.041 | 0.005 |

Vangorp L_la at the trunk under each target's retinal image [cd/m², HDR-VDP local adaptation, extrapolated below its fitted 1 cd/m²] (diagnostic under observer model X):

| target | x0.1 (8.9e-06 lx) | x1 (8.9e-05 lx) | x10 (8.9e-04 lx) | x100 (8.9e-03 lx) |
|---|---|---|---|---|
| ISETBio wvf human, 550 nm, 6 mm, defocus 0 | 0.000374 | 0.00173 | 0.0142 | 0.139 |
| HDR-VDP-3 eye MTF | 0.00332 | 0.0289 | 0.284 | 2.83 |
| CIE 135/1 (Vos-van den Berg 1999), age 24, 4x grid | 0.000433 | 0.00196 | 0.0149 | 0.142 |
| no optics (physical stimulus) | 4.9e-05 | 4.91e-05 | 4.92e-05 | 4.94e-05 |

## DISPLAY ENCODINGS (image D on the phone through the frozen pcond stack, Ldmax 100)

| encoding | evaluator | x0.1 (8.9e-06 lx) | x1 (8.9e-05 lx) | x10 (8.9e-04 lx) | x100 (8.9e-03 lx) |
|---|---|---|---|---|---|
| no optics (physical stimulus) | viewer's eye at the phone | 0.997 | 0.997 | 0.995 | 0.995 |
| no optics (physical stimulus) | optics OFF (diagnostic) | 0.999 | 0.999 | 0.999 | 0.999 |
| Spencer 1995 via Blender Fog Glow | viewer's eye at the phone | 0.744 | 0.173 | 0.012 | 0.000 |
| Spencer 1995 via Blender Fog Glow | optics OFF (diagnostic) | 0.858 | 0.392 | 0.028 | 0.001 |
| Temporal Glare 2009 (Frisvad demo), frame 1 | viewer's eye at the phone | 0.178 | 0.041 wl | 0.033 wl | 0.030 wl |
| Temporal Glare 2009 (Frisvad demo), frame 1 | optics OFF (diagnostic) | 0.362 | 0.274 wl | 0.255 wl | 0.244 wl |
| ISETBio wvf human, 550 nm, 6 mm, defocus 0 (PSF x PSF, informational) | viewer's eye at the phone | 0.955 | 0.664 | 0.144 | 0.014 |
| ISETBio wvf human, 550 nm, 6 mm, defocus 0 (PSF x PSF, informational) | optics OFF (diagnostic) | 0.983 | 0.829 | 0.317 | 0.067 |
| HDR-VDP-3 eye MTF (PSF x PSF, informational) | viewer's eye at the phone | 0.586 | 0.103 | 0.008 | 0.000 |
| HDR-VDP-3 eye MTF (PSF x PSF, informational) | optics OFF (diagnostic) | 0.761 | 0.249 | 0.017 | 0.001 |
| CIE 135/1 (Vos-van den Berg 1999), age 24, 4x grid (PSF x PSF, informational) | viewer's eye at the phone | 0.967 | 0.877 | 0.517 | 0.098 |
| CIE 135/1 (Vos-van den Berg 1999), age 24, 4x grid (PSF x PSF, informational) | optics OFF (diagnostic) | 0.989 | 0.959 | 0.793 | 0.236 |

Plateau: equivalent-area diameter of the pixels with displayed luminance above black >= 0.99 Ldmax [arcmin]; `wl` = window-limited (>= 0.8 of the 57.7' temporal window): neither the plateau nor the P_det is a result there:

| encoding | x0.1 (8.9e-06 lx) | x1 (8.9e-05 lx) | x10 (8.9e-04 lx) | x100 (8.9e-03 lx) |
|---|---|---|---|---|
| no optics (physical stimulus) | 1.9 | 1.9 | 3.2 | 3.2 |
| Spencer 1995 via Blender Fog Glow | 8.3 | 20.7 | 44.7 | 71.8 |
| Temporal Glare 2009 (Frisvad demo), frame 1 | 7.1 | 52.7 wl | 57.9 wl | 59.7 wl |
| ISETBio wvf human, 550 nm, 6 mm, defocus 0 | 6.9 | 10.9 | 19.8 | 41.5 |
| HDR-VDP-3 eye MTF | 11.0 | 26.0 | 53.3 | 87.4 |
| CIE 135/1 (Vos-van den Berg 1999), age 24, 4x grid | 6.7 | 13.4 | 25.1 | 44.9 |

## GAP: |P_det(viewer_eye(D)) - P_det(target_retina)| (display encodings, EVAL_VIEWER)

| encoding D | target | x0.1 (8.9e-06 lx) | x1 (8.9e-05 lx) | x10 (8.9e-04 lx) | x100 (8.9e-03 lx) |
|---|---|---|---|---|---|
| no optics (physical stimulus) | ISET 550 nm (retinal) | 0.722 | 0.909 | 0.970 | 0.988 |
| no optics (physical stimulus) | CIE99 (world, 146 px/deg) | 0.712 | 0.865 | 0.954 | 0.990 |
| no optics (physical stimulus) | HDR-VDP MTF (world, 146 px/deg) | 0.946 | 0.988 | 0.995 | 0.995 |
| Spencer 1995 via Blender Fog Glow | ISET 550 nm (retinal) | 0.469 | 0.085 | 0.013 | 0.007 |
| Spencer 1995 via Blender Fog Glow | CIE99 (world, 146 px/deg) | 0.459 | 0.041 | 0.029 | 0.004 |
| Spencer 1995 via Blender Fog Glow | HDR-VDP MTF (world, 146 px/deg) | 0.693 | 0.164 | 0.012 | 0.000 |
| Temporal Glare 2009 (Frisvad demo), frame 1 | ISET 550 nm (retinal) | 0.097 | 0.047 wl | 0.008 wl | 0.023 wl |
| Temporal Glare 2009 (Frisvad demo), frame 1 | CIE99 (world, 146 px/deg) | 0.107 | 0.091 wl | 0.008 wl | 0.025 wl |
| Temporal Glare 2009 (Frisvad demo), frame 1 | HDR-VDP MTF (world, 146 px/deg) | 0.127 | 0.032 wl | 0.033 wl | 0.030 wl |
