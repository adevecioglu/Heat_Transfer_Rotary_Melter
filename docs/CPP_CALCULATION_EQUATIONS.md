# C++ calculation equations, purpose and provenance

This catalogue describes the native production model. Units are SI internally; engineering temperatures use °C except radiation / IF97, which use kelvin. RPM is revolutions per minute; pressures used for IF97 are absolute.

## Source map

| File | SHA-256 |
| --- | --- |
| [Analysis.cpp](../native/src/Analysis.cpp) | `b28dbac7895f84e2c6fa96e1f04f0a6e83a5f1a3aac93383eed505e31e2c9ad2` |
| [Calculation.cpp](../native/src/Calculation.cpp) | `91970e9875fe1b6d736ce9b356fd0cab05c12c32c8f42685e1c6e08d9542b111` |
| [ContactDynamics.cpp](../native/src/ContactDynamics.cpp) | `c58240bc61ce7bf77e4364fc630fa20a2e3e1cb4a74be1e96e29bd2a8dbde7f7` |
| [Geometry.cpp](../native/src/Geometry.cpp) | `d06eac05903e4b731ca6394bd5642b6e7f6fda5f73fadc27f5ec03d721b00bc4` |
| [Thermodynamics.cpp](../native/src/Thermodynamics.cpp) | `82a9f7d5b05162c1d3af72c0e12d8dbee0f5ed8b4c33e8e5db5e57a45ddade37` |

## 01 · Geometry and charging

Source: [Geometry.cpp:172](../native/src/Geometry.cpp#L172) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Geometry.cpp#L172).

**Stage / purpose:** convert millimetres to metres, establish vessel capacity,
heat-transfer area, water inventory and the actual charged mass before solving.
For radius $R$, cylindrical length $L$, head depth $h$ and head count $n_h$:

$$V=\pi R^2L+n_h\frac{\pi h(3R^2+h^2)}6,\qquad
A=2\pi RL+n_h\pi(R^2+h^2).$$

$$m=V f_{\rm fill}\phi\rho_s\quad\text{(fill mode)},\qquad
m=m_{\rm input}\quad\text{(mass mode)}.$$

$$V_{\rm bulk}=\frac{m}{\rho_s\phi},\quad V_l=\frac{m}{\rho_l},\quad
m_{\max}=\min[V(1-f_{\rm free})\rho_s\phi,V(1-f_{\rm free})\rho_l].$$

The model approximates metal mass as area × thickness × density. Jacket water
volume combines the cylindrical annulus, a thin-gap head approximation and
additional loop litres. These approximations are carried forward from V11;
actual jacket drawings and inventories are required for calibration.

## 02 · Inclined fill and wetted area

Source: [Geometry.cpp:40](../native/src/Geometry.cpp#L40) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Geometry.cpp#L40).

**Stage / purpose:** resolve gravity-oriented fill in inclined cylindrical and
spherical-cap slices, rather than assume every axial region is equally wet.
The cap sphere radius is $R_s=(R^2+h^2)/(2h)$, with local slice radius
$r(z)=\sqrt{R_s^2-(z-z_c)^2}$. For free-surface height $H$ and inclination $\theta$:

$$u=\frac{H-z\sin\theta}{r(z)\cos\theta},\qquad
F_V(u)=\frac12+\frac{\arcsin u+u\sqrt{1-u^2}}\pi,\quad
F_A(u)=\frac12+\frac{\arcsin u}\pi.$$

Both fractions are clipped to 0 / 1 outside $[-1,1]$. In the vertical limit a
height threshold is used. Slice midpoint quadrature evaluates
$\sum\pi r^2\Delta z F_V=fV_q$; **Boost.Math TOMS748** finds the bracketed $H$.
The denominator is the quadrature volume $V_q$, while capacity uses analytic $V$.
Wetted area is $\sum\Delta A F_A/\sum\Delta A$.
These are geometric circle-segment identities, not an empirical material model.

## 03 · Surface grid and phase-dependent wetting

Source: [Geometry.cpp:278](../native/src/Geometry.cpp#L278) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Geometry.cpp#L278).

**Stage / purpose:** distribute areas, capacities and wetting over $A_z$ axial
and $P$ circumferential cells without altering the selected grid.

$$w_a=\frac{\sum_{s\in a}\Delta A_s}{\sum_s\Delta A_s},\quad
A_{a,j}=\frac{Aw_a}{P},\quad C_{a,j}=\frac{m_m c_m w_a}{P}.$$

For a slice, the wetted angular interval is $[\arccos u,2\pi-\arccos u]$.
Intersection with each angular cell gives its wet fraction. Nine precomputed
tables at $f_l=0,1/8,\ldots,1$ use bulk volume
$m[(1-f_l)/(\rho_s\phi)+f_l/\rho_l]$; linear interpolation supplies intermediate
wetting. This is a reduced geometry/phase closure, not a resolved moving fluid interface.

## 04 · Enthalpy, temperature and melting

Source: [Thermodynamics.cpp:9](../native/src/Thermodynamics.cpp#L9) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Thermodynamics.cpp#L9).

**Stage / purpose:** conserve energy through sensible heating and a finite
melting interval. $c_s,c_l$ are J/(kg K), latent heat $\ell$ is J/kg, and
$T_s<T_l$ are solidus/liquidus temperatures in °C. The chosen datum is $h(0)=0$.

$$c_m=\frac{c_s+c_l}{2}+\frac{\ell}{T_l-T_s},\quad
h_s=c_sT_s,\quad h_l=h_s+c_m(T_l-T_s).$$

$$h(T)=\begin{cases}c_sT&T\le T_s\\h_s+c_m(T-T_s)&T_s<T<T_l\\
h_l+c_l(T-T_l)&T\ge T_l.\end{cases}$$

$$T(h)=\begin{cases}h/c_s&h\le h_s\\T_s+(h-h_s)/c_m&h_s<h<h_l\\
T_l+(h-h_l)/c_l&h\ge h_l,\end{cases}\qquad
f_l=\operatorname{clip}\left(\frac{T-T_s}{T_l-T_s},0,1\right).$$

The native state stores $E_i=m_i h_i$ in joules. The enthalpy-method literature
supports the energy formulation [R2]; this particular linear melting law remains
a material approximation that should be replaced by measured DSC data when available.

## 05 · Water properties and saturation

Source: [Thermodynamics.cpp:35](../native/src/Thermodynamics.cpp#L35) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Thermodynamics.cpp#L35).

**Stage / purpose:** evaluate the liquid-state limit and optional water properties
from a published equation of state. **CoolProp/IF97** supplies $p_{sat}(T)$,
$\rho(T,p)$, $c_p(T,p)$ and $\mu(T,p)$, using kelvin and pascal internally [R3].

$$T_K=T_C+273.15,\qquad p_{Pa}=10^5p_{bar},\qquad
T_{ref}=\frac{T_{w,0}+T_{in,set}}2.$$

`constant` preserves the user-provided V11 constants. `if97_reference` evaluates
properties once at $(T_{ref},p_{abs})$ and uses those constants throughout the
conservative solve. It does **not** vary heat capacity independently at each time
step. Reference properties require $p>p_{sat}(T_{ref})$; critical/domain limits are
checked. An inlet pressure below saturation produces an explicit model warning.
The calculation remains a single-phase water model and does not model boiling.

## 06 · Convective and conductive conductances

Source: [Geometry.cpp:324](../native/src/Geometry.cpp#L324) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Geometry.cpp#L324).

**Stage / purpose:** connect water, metal and product using thermal resistances [R1].
For heat flow $Q=G(T_1-T_2)$, conductance $G$ has units W/K.

$$G_{wi}=\frac{A_{heated,k}}{1/h_w+\delta_i/(2k_m)},\quad
G_{wo}=\frac{A_{outer,k}}{1/h_w+\delta_o/(2k_m)},\quad
G_{mp,k}=\frac{A_{heated,k} f_c}{1/h_p+\delta_i/(2k_m)}.$$

Only $G_{mp,k}$ multiplied by current wet fraction transfers heat into product.
Half wall thickness locates metal storage at the wall midplane. Lateral metal
conductance is $k_m A_{cross}/\Delta x$: circumferential
$k_m\delta\Delta z/(R\Delta\varphi)$ and axial
$k_m\delta\pi D/(P\Delta z)$. Thin-wall / equal-length approximations remain explicit.

## 07 · Rotation and effective bed closures

Source: [Geometry.cpp:205](../native/src/Geometry.cpp#L205) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Geometry.cpp#L205).

**Stage / purpose:** represent unresolved rotation-driven heat transfer and
contact topology. These are **calibratable model closures**, not library-certified
correlations or equations directly fitted from a cited rotary drum experiment.

$$s=(n/n_{ref})^b,\qquad
h_p=\begin{cases}h_{ref}(1+g_rs)&\text{legacy mode}\\
\min[h_{lim},h_{static}+(h_{ref}-h_{static})s]&\text{bounded mode}.\end{cases}$$

$$k_c=\frac{k_s}{1+R_c k_s/d_p},\quad \phi_f=\phi+(1-\phi)f_l,\quad
k_{solid}=k_c(1-f_l)+k_l f_l,\quad k_{pore}=k_g(1-f_l)+k_l f_l.$$

$$k_{series}=\left(\frac{\phi_f}{k_{solid}}+\frac{1-\phi_f}{k_{pore}}\right)^{-1},\quad
k_{parallel}=\phi_f k_{solid}+(1-\phi_f)k_{pore},\quad
k_{bed}=k_{series}+\chi(k_{parallel}-k_{series}).$$

$$G_{bed}=\frac{k_{bed}V_{bed}^{2/3}}{\max(d_p,\lambda D)},\quad
\dot m_{ex}=m\epsilon_{rev}n/60,\quad G_{mix}=\dot m_{ex}c_l,\quad
Bi=\frac{h_p d_p}{6k_s}.$$

Series/parallel thermal bounds supply an interpretable range; $\chi$, $R_c$,
$\lambda$, the RPM law and exchange per revolution need equipment/material data.
`Gmix` is reported for diagnostics and the stability estimate; actual interpopulation
exchange acts on enthalpy in Stage 09, avoiding double-counting it as a second heat path.
Rotating-bed regime literature [R7] motivates caution, not numerical calibration.

## 08 · Radial finite-volume granules

Source: [Geometry.cpp:382](../native/src/Geometry.cpp#L382) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Geometry.cpp#L382).

**Stage / purpose:** resolve internal granule gradients instead of assuming each
granule is isothermal. Two representative populations share $K$ concentric shells.

$$\Delta r=R_p/K,\quad w_j=\frac{(j+1)^3-j^3}{K^3},\quad
m_{p,j}=m_p w_j,\quad N_p=\frac{m_p}{\rho_s(4\pi R_p^3/3)}.$$

$$k_j=(1-f_{l,j})k_s+f_{l,j}k_l,\quad
G_{j+1/2}=N_p\frac{4\pi r_{j+1/2}^2}{\Delta r}
\frac{2k_j k_{j+1}}{k_j+k_{j+1}},\quad
Q_{j\leftarrow j+1}=G_{j+1/2}(T_{j+1}-T_j).$$

Each internal flux is added to one shell and subtracted from its neighbour.
The surface half-cell conductance is $N_p4\pi R_p^2k_{K-1}/(\Delta r/2)$.
Fourier conduction and conservative control-volume balances underpin this discretization [R1].

## 09 · Coupled surface balance and population exchange

Source: [Calculation.cpp:106](../native/src/Calculation.cpp#L106) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Calculation.cpp#L106).

**Stage / purpose:** find the near-wall and core population surface temperatures
without adding a fictitious massless-surface heat capacity. Let
$F=\sum_kG_{mp,k}f_{wet,k}$ and $B=G_{bed}$.

$$\begin{bmatrix}G_n+F+B&-B\\-B&G_c+B\end{bmatrix}
\begin{bmatrix}T_{ns}\\T_{cs}\end{bmatrix}=
\begin{bmatrix}G_nT_{n,K-1}+\sum_kG_{mp,k}f_{wet,k}T_{i,k}\\G_cT_{c,K-1}\end{bmatrix}.$$

**Eigen LDLT** solves this symmetric positive definite 2×2 system. Non-finite
solutions are rejected. Film flux is $G_{mp,k}f_{wet,k}(T_{i,k}-T_{ns})$;
bed flux is $B(T_{ns}-T_{cs})$.

$$Q_{ex,j}=\dot m_{ex}w_j(h_{n,j}-h_{c,j}),\quad
\dot E_{n,j}\mathrel{-}=Q_{ex,j},\quad\dot E_{c,j}\mathrel{+}=Q_{ex,j}.$$

Exchange transfers energy with equal and opposite signs. It is a reduced
renewal assumption; mechanical trajectories do not independently validate it.

## 10 · Water circuit and source boundary

Source: [Calculation.cpp:134](../native/src/Calculation.cpp#L134) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Calculation.cpp#L134).

**Stage / purpose:** retain finite water inventory and serial jacket advection,
including the initially cold return and metal, rather than impose instant hot water everywhere.

$$\dot C_w=\rho_w\dot V c_{p,w},\quad
Q_{req}=\max[0,\dot C_w(T_{set}-T_{out})],\quad
Q_s=\begin{cases}Q_{req}&\text{fixed inlet}\\\min(Q_{req},\eta P_b)&\text{power limited}.\end{cases}$$

$$T_{in}=T_{out}+Q_s/\dot C_w,\quad
C_{w,a}\dot T_{w,a}=\dot C_w(T_{up,a}-T_{w,a})
-\sum_j(Q_{wi,a,j}+Q_{wo,a,j})-UA_{extra}w_a(T_{w,a}-T_{amb}).$$

For the first water zone $T_{up}=T_{in}$; subsequent zones use the preceding
water zone. $C_{w,a}=\rho_wc_{p,w}V_w w_a$.
Fixed inlet mode reports the required instantaneous power even if it exceeds
the nominal boiler entry. Source energy before efficiency is $E_s/\eta$;
the integrated $E_s$ is energy actually delivered to the modelled water.

## 11 · Metal conduction, advection and storage

Source: [Calculation.cpp:141](../native/src/Calculation.cpp#L141) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Calculation.cpp#L141).

**Stage / purpose:** evolve inner/outer metal temperatures, including rotation
and axial/circumferential diffusion. Inner metal follows

$$C_{i,k}\dot T_{i,k}=Q_{wi,k}-Q_{mp,k}
+\sum_{l\in\mathcal N(k)}G_{kl}(T_{i,l}-T_{i,k})
+C_{i,k}\omega_P(T_{i,up}-T_{i,k}),\qquad\omega_P=nP/60.$$

Outer metal replaces the product term with exterior convection plus radiation.
Angular indices are periodic and the upstream index follows `rotationDirection`.
No axial neighbour is added across an end boundary. This is a first-order
upwind rotation model with numerical diffusion, not a resolved material mesh.
Cell updates gather old-state neighbours and write only their own derivatives;
this makes the optional OpenMP surface loop race free.

## 12 · Exterior convection, radiation and insulation

Source: [Thermodynamics.cpp:57](../native/src/Thermodynamics.cpp#L57) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Thermodynamics.cpp#L57).

**Stage / purpose:** account for ambient heat exchange and insulation resistance.

$$Q_{conv}=h_{ext}A(T_s-T_{amb}),\qquad
Q_{rad}=\varepsilon\sigma A[(T_s+273.15)^4-(T_{amb}+273.15)^4],\quad
\sigma=5.670374419\times10^{-8}\ {\rm W\,m^{-2}K^{-4}}.$$

$$G_{ins}=k_{ins}A/\delta_{ins},\qquad
G_{ins}(T_{metal}-T_s)=Q_{conv}(T_s)+Q_{rad}(T_s).$$

With no insulation $T_s=T_{metal}$. Otherwise **Boost.Math TOMS748** solves for
$T_s$ bracketed by metal and ambient temperatures. Negative flux naturally
means heat enters a colder vessel. Newton cooling, Fourier resistance and the
Stefan–Boltzmann law provide the physical basis [R1]; emissivity and external $h$
are input assumptions and require appropriate surface/flow data.

## 13 · Stable step and library integration

Source: [Calculation.cpp:350](../native/src/Calculation.cpp#L350) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Calculation.cpp#L350).

**Stage / purpose:** advance the conservative state using tested numerical
algorithms from **Boost.Odeint**, keeping dependent time steps sequential [R4].
The default RK2 midpoint rule preserves the V11 time-integration convention:

$$k_1=f(t_n,y_n),\quad k_2=f(t_n+\Delta t/2,y_n+\Delta t k_1/2),\quad
y_{n+1}=y_n+\Delta t k_2.$$

Alternatives use Odeint `runge_kutta4` or controlled `runge_kutta_dopri5`.
The latter uses an embedded error estimate and user tolerances, but its proposed
step is still capped by the conservative explicit-stability limit. It is not
an implicit stiff solver.

$$\Delta t\le\min\left(\Delta t_{input},\,0.16\frac{C_i}{\sum G_i},\,
0.12\frac{m_j\min(c_s,c_l)}{\sum G_j+\dot m_{ex}w_j\min(c_s,c_l)}\right).$$

Water advection, metal rotation and $4\varepsilon\sigma T_{max,K}^3$ radiation
linearization enter the conductance sums. The safety factors are retained V11
implementation choices, not universal stability theorems. Each RK stage also
integrates source/loss energies, maintaining consistent accounting. Finite-state,
cancellation and explicit wall-time-budget checks reject invalid/incomplete runs.

## 14 · Conservation, target and exported quantities

Source: [Calculation.cpp:428](../native/src/Calculation.cpp#L428) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Calculation.cpp#L428).

**Stage / purpose:** explain measured outputs and detect accounting defects.

$$\Delta E_p=\sum_i(E_i-m_i h(T_0)),\quad
\Delta E_m=\sum_k C_{i,k}(T_{i,k}-T_{m,0})+C_{o,k}(T_{o,k}-T_{m,0}),$$

$$\Delta E_w=\sum_a C_{w,a}(T_{w,a}-T_{w,0}),\quad
R_E=E_s-E_{loss}-\Delta E_p-\Delta E_m-\Delta E_w,$$

$$r_E=\frac{|R_E|}{\max(1\ {\rm J},|E_s|,
|\Delta E_p|+|\Delta E_m|+|\Delta E_w|+|E_{loss}|)}.$$

All energy integrals use joules internally; divide by $3.6\times10^6$ for kWh.
Target is reached only when **every shell in both populations** has
$E_i\ge m_i h(T_{target})$. Reported target time is the first accepted integration
endpoint satisfying that condition; it has finite time-step resolution.
The reported centre temperature is the colder of the two innermost shell values.
Melting time uses the same all-shell criterion at liquidus. Mass-weighted
$\sum m_i f_{l,i}/m$ gives total liquid fraction. The instantaneous water audit is
$\dot C_w(T_{in}-T_{out})-Q_{water\to metal}-Q_{extra}-\dot E_w$.
Small conservation residual demonstrates accounting consistency, not experimentally
accurate heat-transfer coefficients or melt time.

## 15 · Pipe/annulus hydraulics

Source: [Geometry.cpp:64](../native/src/Geometry.cpp#L64) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Geometry.cpp#L64).

**Stage / purpose:** estimate pressure loss and pump demand alongside thermal
results, using the entered route rather than treating supply/return as a single diameter.

$$A_f=\pi(D_o^2-D_i^2)/4,\quad D_h=D_o-D_i,\quad
v=\dot V/A_f,\quad Re=\rho vD_h/\mu.$$

For pipe flow $f_D=64/Re$ in laminar conditions. For an annulus with
$\beta=D_i/D_o$ the implemented Poiseuille factor is

$$f_DRe=\frac{64(1-\beta)^2(1-\beta^2)}
{1-\beta^4-(1-\beta^2)^2/\ln(1/\beta)}.$$

For turbulence, **Boost.Math TOMS748** solves Colebrook's implicit Darcy factor [R5]:

$$\frac1{\sqrt{f_D}}=-2\log_{10}\left(\frac{\epsilon/D_h}{3.7}
+\frac{2.51}{Re\sqrt{f_D}}\right),\quad
\Delta p=\left(f_D\frac{L}{D_h}+K\right)\frac{\rho v^2}{2}.$$

Between $Re=2300$ and 4000 a linear blend connects laminar/turbulent estimates;
this transitional blend is a numerical assumption. Jacket annulus and lumped
joint/equipment losses are approximations. Total head is $\Delta p/(\rho g)$,
hydraulic power $\dot V\Delta p$ and input power $\dot V\Delta p/\eta_p$.
Absence of component loss data is reported; this model is not a vendor pump curve.

## 16 · Spatial, temporal and radial analysis

Source: [Analysis.cpp:37](../native/src/Analysis.cpp#L37) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/Analysis.cpp#L37).

**Stage / purpose:** separate discretization effects and avoid a false precision claim.
Coarse/base/fine surface meshes use ratio $r=2$ in both directions, identical
radial resolution and a common stable time step. Separate runs halve $\Delta t$
and double radial shells. Independent cases use **BS_thread_pool**, bounded by
the requested thread count; each inner case is serial to avoid oversubscription.

For coarse $F_3$, medium $F_2$ and fine $F_1$:

$$p=\frac{\ln|(F_3-F_2)/(F_2-F_1)|}{\ln2},\quad
F_{ext}=F_1+\frac{F_1-F_2}{2^p-1},\quad
GCI_1=1.25\frac{|(F_1-F_2)/F_1|}{2^p-1}.$$

These are conditional Richardson/GCI estimates [R6]. The implementation omits
GCI for oscillatory/non-contracting differences, zero/invalid quantities, and
target-time differences below two common steps. Target-time comparisons require
all relevant runs to reach target. Failure to reach target is not a zero error.
Sensitivity cases perturb RPM, flow, reference film coefficient and exchange
per revolution by ±10%; these compare assumptions, not probability distributions.
For each parameter $p$ and response $F$ the local dimensionless elasticity is

$$S_{F,p}=\frac{F(p_+)-F(p_-)}{p_+-p_-}\frac{p_0}{F(p_0)}.$$

The actual clipped parameter span is used. Zero spans/responses, invalid cases
and unreached targets receive an explicit unavailable reason instead of an elasticity.
Boiler sizing refines a bracket sequentially because each new bound depends on
the previous solve. A 1000 kW upper search bound and 16 refinements are explicit
algorithm limits, not evidence that the physical equipment can deliver that power.

## 17 · Granule initialization and wall geometry

Source: [ContactDynamics.cpp:315](../native/src/ContactDynamics.cpp#L315) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/ContactDynamics.cpp#L315).

**Stage / purpose:** initialize actual-size spherical particles without imposing
orbital co-rotation. The number of particles is nearest-integer
$N=m/[\rho_s(4\pi r_0^3/3)]$, and remaining solid radius is
$r=r_0(1-f_l)^{1/3}$. A 1.025-spaced FCC lattice has cell size
$a=2\sqrt2r\times1.025$ and four standard face-centred basis points.
Only centres with wall clearance $>1.005r$ are eligible; the lowest
$y\cos\theta+z\sin\theta$ values are selected using a stable order.
This deterministic tie order can differ from V11 NumPy's unspecified quicksort ties.
The nearest cylinder, spherical-cap arc or end disk yields signed wall distance
and outward normal. A linked-cell list with width $2.25r$ searches 27 neighbours;
it changes search cost, not sphere radius. No arbitrary visual particle-count cap
is used; an explicit allocation budget rejects infeasible allocations.

## 18 · Rigid-granule contact dynamics

Source: [ContactDynamics.cpp:93](../native/src/ContactDynamics.cpp#L93) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/ContactDynamics.cpp#L93).

**Stage / purpose:** model rigid nonpenetration, restitution, Coulomb friction and
sphere spin. The method is an application-specific sequential-impulse solver
using Eigen vectors; constraint principles are described by Catto [R8].

$$\mathbf a=(0,-g\cos\theta,-g\sin\theta)(1-f_l\rho_l/\rho_s)
+d f_l(\mathbf v_{carrier}-\mathbf v),\quad
\mathbf v_{carrier}=(-\omega s y,\omega s x,0).$$

For relative contact velocity $\mathbf v_c$, inward normal $\mathbf n$,
gap $s_n$ and step $\Delta t$:

$$v_{target}=0.2\frac{\max(-s_n-0.0002r,0)}{\Delta t}
-\frac{\max(s_n,0)}{\Delta t},\quad
\lambda_n^{new}=\max[0,\lambda_n+(v_{target}-\mathbf v_c\cdot\mathbf n)/m_{eff}^{-1}].$$

Restitution additionally requires closing speed below −0.15 m/s and near contact.
With unit-mass normalized particles, $m_{eff}^{-1}=2$ for pairs and 1 for walls.
Tangential effective inverse masses are 7 and 3.5, using sphere inertia
$I=2mr^2/5$. Accumulated tangential impulse is projected onto
$\|\boldsymbol\lambda_t\|\le\mu\lambda_n$.
Equal/opposite linear impulses and corresponding spin changes preserve pair
linear and angular momentum. Warm starts are reused only from the preceding step.
Alternating sequential sweeps are followed by split position corrections with
0.4 pair and 0.8 wall factors; these do not alter kinetic velocities. The residual
overlap is a numerical constraint error, not physical material strain.
Shared-particle constraints are deliberately not parallelized.

## 19 · Compliant elastic-contact alternative

Source: [ContactDynamics.cpp:187](../native/src/ContactDynamics.cpp#L187) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/ContactDynamics.cpp#L187).

**Stage / purpose:** retain the V11 damped linear-contact alternative for comparison.
This model is not a measured constitutive law for wax or chocolate.

$$\zeta=\frac{-\ln e}{\sqrt{\pi^2+(\ln e)^2}},\quad
\gamma=2\zeta\sqrt{k_n},\quad k_t=\alpha_t k_n,\quad
F_n=\max(0,k_n\delta-\gamma_{pair}v_n),\quad\gamma_{pair}=\gamma/\sqrt2.$$

Tangential displacement history is projected onto the current tangent plane and
advanced by $\mathbf v_t\Delta t$. The trial force
$\mathbf F_t=-k_t\boldsymbol\xi-\gamma_{pair}\mathbf v_t$ is clipped to
$\|\mathbf F_t\|\le\mu F_n$ and the history corrected consistently.
Wall normals use the outward sign convention, so the damping sign is adjusted.
Rolling damping opposes spin and is capped at $1/\Delta t$.
Semi-implicit Euler updates velocity then position; the Python transport caps the
compliant step at $0.15/\sqrt{k_n}$. Stiffness is acceleration-normalized by unit mass,
as in the reference; it must not be mistaken for a certified dimensional modulus.

## 20 · Interstitial liquid display plane

Source: [ContactDynamics.cpp:342](../native/src/ContactDynamics.cpp#L342) · [GitHub source](https://github.com/adevecioglu/Heat_Transfer_Rotary_Melter/blob/main/native/src/ContactDynamics.cpp#L342).

**Stage / purpose:** place a static liquid display plane around occupied spheres.
This calculation is not a free-surface CFD solution.

$$V_{void}(H)=V_{vessel,below}(H)-\sum_i\pi c_i^2(r-c_i/3),\quad
c_i=\operatorname{clip}[H-(y_i\cos\theta+z_i\sin\theta)+r,0,2r],$$

$$V_{void}(H)=m f_l/\rho_l.$$

The first term uses 600 vessel slices. **Boost.Math TOMS748** replaces the manual
38-step bisection for the liquid-plane root, with an explicit check that volume
fits in the void space. Buoyancy/drag remain a selected-phase approximation;
there is no solved liquid pressure or velocity field.

## Literature and numerical libraries

- **[R1]** MIT Unified Engineering, [Heat transfer notes](https://web.mit.edu/16.unified/www/SPRING/propulsion/notes/node123.html): conduction, convection and thermal resistance concepts. Classical energy balances and Stefan–Boltzmann radiation are used with stated project geometry approximations.
- **[R2]** Voller, Cross & Markatos (1987), *An enthalpy method for convection/diffusion phase change*, [DOI:10.1002/nme.1620240119](https://doi.org/10.1002/nme.1620240119). Supports enthalpy formulation, not the project-specific linear DSC approximation.
- **[R3]** IAPWS, [Industrial formulation IF97](https://iapws.org/relguide/IF97-Rev.html); [CoolProp/IF97 v2.2.1](https://github.com/CoolProp/IF97/tree/v2.2.1). Native saturation/thermophysical implementation; input unit conversions and liquid-state checks remain application responsibilities.
- **[R4]** Boost, [Odeint steppers](https://www.boost.org/doc/libs/latest/libs/numeric/odeint/doc/html/boost_numeric_odeint/odeint_in_detail/steppers.html) and [TOMS748 root finding](https://www.boost.org/doc/libs/latest/libs/math/doc/html/math_toolkit/roots_noderiv/TOMS748.html). These replace numerical algorithms; they do not supply the vessel's physical model.
- **[R5]** Colebrook (1939), *Turbulent flow in pipes, with particular reference to the transition region between the smooth and rough pipe laws*, [DOI:10.1680/ijoti.1939.13150](https://doi.org/10.1680/ijoti.1939.13150). Hydraulic-diameter application to the actual jacket remains an engineering approximation.
- **[R6]** NASA NPARC, [Examining Spatial (Grid) Convergence](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html). Richardson extrapolation, observed order and conditional GCI; not experimental validation.
- **[R7]** Mellmann (2001), *The transverse motion of solids in rotating cylinders—forms of motion and transition behavior*, [DOI:10.1016/S0032-5910(00)00402-2](https://doi.org/10.1016/S0032-5910(00)00402-2). Regime context only; the custom RPM/contact coefficients are not derived from this paper.
- **[R8]** Erin Catto, [Modeling and Solving Constraints (2009)](https://box2d.org/files/ErinCatto_ModelingAndSolvingConstraints_GDC2009.pdf) and [Solver2D (2024)](https://box2d.org/posts/2024/02/solver2d/). Constraint/impulse principles; the application is a custom 3D sphere implementation, not a claim that Box2D solves this vessel.
- **[L1]** [Eigen 5.0.0](https://libeigen.gitlab.io/): LDLT and vector algebra. Its compatibility macros still read 3.5.0; the downloaded release is 5.0.0.
- **[L2]** [BS_thread_pool 5.1.0](https://github.com/bshoshany/thread-pool/tree/v5.1.0): independent-case scheduling.
- **[L3]** [nlohmann/json 3.12.0](https://github.com/nlohmann/json/tree/v3.12.0): typed JSON boundary; not a physics package.

Exact download URLs and SHA-256 values: [dependencies.lock.json](../native/dependencies.lock.json).

## Reading results and reproducing a run

The dashboard exposes `midpoint`, `rk4`, `dopri5`, thread count and water-property
mode. Each successful run stores `result.json`, `history.csv`, `run_manifest.json`
and `RUN_REPORT.md` under `outputs/runs/<run-id>/`. Input and request hashes,
compiled-source fingerprint and native DLL hash identify what ran. The requested
configuration is preserved separately from derived effective mass/properties.
Reopening a run restores its inputs and result; editing invalidates its displayed
current-result status. A stopped run is not reported as a completed target.

```powershell
.venv\Scripts\python.exe -m tools.BuildCpp
.venv\Scripts\python.exe app.py --run --output outputs\cpp_run
.venv\Scripts\python.exe app.py --analyse convergence --threads 4 --output outputs\cpp_convergence
.venv\Scripts\python.exe -m tools.DocumentCppEquations --check
```

The independent Python/SciPy reference in `rotary_melter/Calculation.py` is retained;
its equation catalogue remains [CALCULATION_EQUATIONS.md](CALCULATION_EQUATIONS.md).
The V11 JavaScript model is retained for reproducible regression via
`app.py --run --engine javascript`. The dashboard uses the native C++ engine.

**Limits:** heat-transfer/contact closures and material inputs need experimental
calibration; numerical conservation and agreement with the previous implementation
do not establish real equipment performance. Mechanics use selected thermal phase
one way; they do not automatically calibrate thermal conductance. A library replaces
appropriate numerical/property algorithms while explicit physical balances remain
readable and inspectable in the project source.
