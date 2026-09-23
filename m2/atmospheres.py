"""M2 atmospheres: homogeneous boundary-layer media from physical parameters, built with
Cycles' stock Volume Coefficients node (Beer-Lambert per channel verified by
m2/calibrate_volume.py). Nothing here is a new scattering model; it only turns textbook
optical parameters into per-channel coefficients:

  total extinction at 550 nm from meteorological visibility (Koschmieder, 2 % contrast
  threshold):  sigma_ext(550) = 3.912 / V
  Rayleigh (sea-level air, 550 nm) sigma_R = 1.16e-5 1/m, lambda^-4, Rayleigh phase
  aerosol = the rest: Angstrom exponent alpha (lambda^-alpha), single-scattering albedo w,
            Henyey-Greenstein g (sub-micron haze; Cycles' Mie phase is for 0-50 um water
            droplets, i.e. mist/fog, not haze)
  RGB channels are represented by effective wavelengths 610 / 550 / 465 nm.
  Medium: slab from the ground to LAYER_TOP (well-mixed boundary layer); above it the
  authored sky radiance is used unchanged.
"""
import bpy

LAMBDA = (610.0, 550.0, 465.0)
SIGMA_RAYLEIGH_550 = 1.16e-5
LAYER_TOP = 1000.0               # m

CASES = {  # visibility V [m], Angstrom alpha, single-scattering albedo, HG g
    "clear": dict(V=40_000.0, alpha=1.3, ssa=0.90, g=0.70),
    "mild": dict(V=15_000.0, alpha=1.3, ssa=0.90, g=0.70),
    "moderate": dict(V=7_000.0, alpha=1.3, ssa=0.90, g=0.70),
}


def coefficients(V, alpha, ssa, g):
    """-> (aerosol absorption RGB, aerosol scattering RGB, Rayleigh scattering RGB, g)."""
    aer550 = 3.912 / V - SIGMA_RAYLEIGH_550
    aer = [aer550 * (l / 550.0) ** -alpha for l in LAMBDA]
    ray = [SIGMA_RAYLEIGH_550 * (l / 550.0) ** -4 for l in LAMBDA]
    return [a * (1 - ssa) for a in aer], [a * ssa for a in aer], ray, g


def add_boundary_layer(scene, case, extent=(60_000.0, 60_000.0), centre_y=15_000.0):
    sa, ss, sr, g = coefficients(**case)
    m = bpy.data.materials.new("BoundaryLayer")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    aer = nt.nodes.new("ShaderNodeVolumeCoefficients")
    aer.phase = "HENYEY_GREENSTEIN"
    aer.inputs["Absorption Coefficients"].default_value = sa
    aer.inputs["Scatter Coefficients"].default_value = ss
    aer.inputs["Anisotropy"].default_value = g
    ray = nt.nodes.new("ShaderNodeVolumeCoefficients")
    ray.phase = "RAYLEIGH"
    ray.inputs["Absorption Coefficients"].default_value = (0.0, 0.0, 0.0)
    ray.inputs["Scatter Coefficients"].default_value = sr
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(aer.outputs[0], add.inputs[0])
    nt.links.new(ray.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Volume"])
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, centre_y, LAYER_TOP / 2 - 1.0))
    slab = bpy.context.active_object
    slab.scale = (extent[0], extent[1], LAYER_TOP + 2.0)   # starts 1 m below the ground plane
    slab.data.materials.append(m)
    slab.name = "BoundaryLayer"
    return sa, ss, sr


if __name__ == "__main__":
    for k, c in CASES.items():
        sa, ss, sr, g = coefficients(**c)
        ext = [a + b + r for a, b, r in zip(sa, ss, sr)]
        print(f"{k:9s} V={c['V'] / 1000:4.0f} km  extinction RGB [1/m] {[f'{x:.2e}' for x in ext]}  "
              f"T(5 km) {[round(pow(2.718281828, -x * 5000), 3) for x in ext]}  "
              f"T(14 km) {[round(pow(2.718281828, -x * 14000), 3) for x in ext]}")
