#!/usr/bin/env bash
# Minimal repro: pcond -x reports display luminance WHTEFFICACY/Ldmax too high in linear mode.
# Radiance tools only. Tested with Radiance master bcffc2b (2026-08-19 CVS import).
#
# pcond(1): "-x mapfile ... their corresponding display luminance values (also in cd/m^2)".
# Output pixel value v relates to display luminance by the model pcond itself uses:
#   histogram mode (mapscan): v = (Ld - Ldmin)/(Ldmax - Ldmin)  ->  Ld = Ldmin + v*(Ldmax-Ldmin)
#   linear mode   (sfscan):   v = scalef*radiance, scalef = s0*179/(inpexp*Ldmax) -> Ld = Ldmax*v
# Observed: histogram mode, -x matches (ratio 1). Linear mode (-l, -e, or pcond's automatic
# fallback when the histogram needs no compression), -x is too high by 179/Ldmax: the ratio
# follows -u exactly (100/179 = 0.559, 50/179 = 0.279). putmapping() prints sf*wlum with
# sf = scalef*inpexp, and scalef already contains WHTEFFICACY/(inpexp*Ldmax).
set -euo pipefail
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT; cd "$T"

# 600x10 grey ramp, world luminance 1e-3 .. 1e3 cd/m^2 (radiance = L/179), 60 deg view
pcomb -x 600 -y 10 -e 'L=10^(-3+6*(x+.5)/600); v=L/179; ro=v; go=v; bo=v' > ramp0.hdr
getinfo -a "VIEW= -vtv -vh 60 -vv 1" < ramp0.hdr > ramp.hdr

check() { # ldmax pcond flags...
  local ldmax=$1; shift
  pcond -u "$ldmax" "$@" -x map.dat ramp.hdr > out.hdr
  pvalue -h -H -b -d out.hdr | sed -n '3001,3600p' > lum.txt          # row 5, 600 pixels
  awk -v ldmax="$ldmax" '
    BEGIN { ldmin = ldmax/100 }                                       # default -d 100
    NR==FNR { w[NR]=$1; d[NR]=$2; n=NR; next }                        # map.dat
    { L=10^(-3+6*(FNR-.5)/600)
      for (i=1;i<n;i++) if (w[i]<=L && L<w[i+1]) {
        t=(log(L)-log(w[i]))/(log(w[i+1])-log(w[i])); m=d[i]+t*(d[i+1]-d[i])
        if (m>1.5*ldmin && m<0.99*ldmax) { h+=(ldmin+$1*(ldmax-ldmin))/m; l+=ldmax*$1/m; c++ } } }
    END { printf "  %4d px: histogram-model ratio %.4f, linear-model ratio %.4f   (Ldmax/179 = %.4f)\n",
          c, h/c, l/c, ldmax/179 }' map.dat lum.txt
}
echo "histogram mode, pcond -s -u 100  (expect histogram-model ratio 1):"; check 100 -s
echo "linear mode,    pcond -l -u 100  (linear-model ratio = 100/179 -> bug):"; check 100 -l
echo "linear mode,    pcond -l -u 50   (linear-model ratio = 50/179  -> bug):"; check 50 -l
echo "linear mode,    pcond -e +2 -u 100:"; check 100 -e +2
