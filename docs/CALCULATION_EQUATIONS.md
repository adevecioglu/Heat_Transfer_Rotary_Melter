# Rotary Melter V11 — calculation equations and sources

This catalogue covers every equation in the independent Python [Calculation.py](../rotary_melter/Calculation.py), including geometry, hydraulic checks, numerical differentiation and comparison criteria. It also identifies the corresponding production JavaScript equations and additional rotation/RPM/GCI formulas. It describes the V11 rotary model, rather than importing the earlier Mixing Vessel physics.

Source-line links identify the start of each calculation; adjacent ranges identify its implementation. Recheck these references after editing sources. All equations are written with KaTeX-compatible Markdown delimiters. Open this file in VS Code and press **Ctrl+Shift+V**, or choose **Markdown Preview Enhanced: Open Preview to the Side**. The math extension and workspace settings are prepared.

**Attribution:** “derived” means an algebraic consequence of the implemented geometry or conservation law. “Project closure” marks assumptions that require calibration. A literature citation supports its stated physical/methodological basis, not every project parameter or the complete equipment model. Shared coefficients in the Python and JavaScript solvers do not establish experimental validation.

## 1. Symbols and scope

| Symbol | Meaning | SI unit |
| --- | --- | --- |
| $T,T_s,T_l,T_a$ | Temperature, solidus, liquidus, ambient | °C |
| $h,c_s,c_l,L_h$ | Specific enthalpy, solid/liquid heat capacities, latent heat | J/kg; J/(kg K) |
| $R,L,H_c,R_s$ | Vessel radius, cylinder length, head depth, spherical-head radius | m |
| $A,P,N,K$ | Axial zones, angular zones, surface cells, radial shells per population | counts |
| $m_i,C_i$ | Shell mass, metal/water node heat capacity | kg, J/K |
| $G,F$ | Thermal conductance, water heat-capacity flow rate | W/K |
| $Q_v,\dot m$ | Volumetric flow, mass flow | m³/s, kg/s |
| $q,\dot Q$ | Heat transfer rate | W |
| $f,\beta_i,\phi$ | Mass-average liquid fraction, shell liquid fraction, effective bed solid fraction | dimensionless |
| $\theta,\omega$ | Vessel axis inclination from horizontal, angular speed | rad, rad/s |
| $\mathbf y$ | ODE state: shell enthalpies, node temperatures, five integrated energies | mixed units |

The product has two spherical-granule populations: near-wall and core. Metal/water temperature nodes lie on an axial/angular surface network. Occupancy, contact and material data are shared exported coefficients. The model does not solve a liquid velocity/pressure CFD field. Native particle mechanics are a separate model; their overlaps are not silently converted into a calibrated thermal contact law.

## 2. Enthalpy, inverse temperature and liquid fraction

**Code:** [`enthalpy` and `temperature`, lines 11–16](../rotary_melter/Calculation.py#L11); [phase calculation, line 34](../rotary_melter/Calculation.py#L34). **Basis:** enthalpy methods [R1](https://doi.org/10.1002/nme.1620240119); exact piecewise choices are the implementation's constitutive law.

$$
c_m=\frac{c_s+c_l}{2}+\frac{L_h}{T_l-T_s},\qquad
h_s=c_sT_s,\qquad h_l=h_s+c_m(T_l-T_s).
\tag{C01}
$$

$$
h(T)=\begin{cases}c_sT,&T\leq T_s,\\h_s+c_m(T-T_s),&T_s<T<T_l,\\h_l+c_l(T-T_l),&T\geq T_l,\end{cases}
\quad
T(h)=\begin{cases}h/c_s,&h\leq h_s,\\T_s+(h-h_s)/c_m,&h_s<h<h_l,\\T_l+(h-h_l)/c_l,&h\geq h_l.\end{cases}
\tag{C02}
$$

$$
\beta_i=\min\left(1,\max\left(0,\frac{T_i-T_s}{T_l-T_s}\right)\right),\qquad
f=\frac{\sum_i m_i\beta_i}{m_{\rm total}}.
\tag{C03}
$$

The latent heat is included once in $c_m$. Here `cm` already includes the latent contribution; it is not just the average sensible heat capacity. Enthalpy is relative to solid at 0 °C. Constant properties and linear phase fraction are project assumptions.

## 3. State layout, initial conditions and conservative links

**Code:** [`solve`, lines 18–32](../rotary_melter/Calculation.py#L18). **Basis:** energy conservation; independently assembled ODEs with shared exported coefficients.

$$
N=AP,\qquad B=2K,\qquad D=B+2N+A,\qquad
\mathbf y=(\mathbf h_{2K},\mathbf T_{i,N},\mathbf T_{w,A},\mathbf T_{o,N},E_{\rm in},E_{\rm loss},E_{\rm conv},E_{\rm rad},E_{\rm extra}).
\tag{C04}
$$

$$
h_i^0=h(T_{\rm product,0}),\quad T_{i,j}^0=T_{o,j}^0=T_{\rm metal,0},\quad
T_{w,a}^0=T_{\rm water,0},\quad E_{\rm integrated}^0=0.
\tag{C05}
$$

Temperature-vector offsets are `wi=N`, `oi=N+A`; full-state temperature entries start at $B$. `Ci`, `Cj`, `Co` and shell masses are supplied by the exported thermal specification, rather than recomputed independently here.

$$
\dot Q_{a\to b}=G(T_a-T_b),\qquad
\begin{bmatrix}\dot E_a\\\dot E_b\end{bmatrix}
=G\begin{bmatrix}-1&1\\1&-1\end{bmatrix}\begin{bmatrix}T_a\\T_b\end{bmatrix}.
\tag{C06}
$$

`link()` adds this pairwise flux matrix, preserving the sum of energy rates. It connects each inner/outer steel cell to its water zone, angular neighbors cyclically, and adjacent axial cells. Missing axial boundary links mean no heat exchange through those omitted faces. Conductance physics follows [R2, MIT resistance-network discussion](https://web.mit.edu/16.unified/www/SPRING/propulsion/notes/node123.html); the network topology is project specific.

$$
\dot E_{w,a}^{\rm flow}=F(T_{w,(a-1)\bmod A}-T_{w,a}),\qquad
\dot E_{m,a,j}^{\rm rotation}=C_{m,a,j}\Omega(T_{m,a,(j+s)\bmod P}-T_{m,a,j}).
\tag{C07}
$$

Here $s$ is `rotationDirection`; $\Omega$ is exported `rotationRate`, an angular-cell transport rate, not necessarily the physical rad/s directly. The same rotation transport is applied to both metal surfaces. The water matrix forms a recirculating chain; the source below supplies its temperature increase. These are the actual matrix terms in lines 25–29.

## 4. Occupancy interpolation and radial shell conduction

**Code:** [`rhs`, lines 33–40](../rotary_melter/Calculation.py#L33). **Derived interpolation and conductive fluxes.**

$$
x=\min(8,\max(0,8f)),\quad j=\min(7,\lfloor x\rfloor),\quad b=x-j,\qquad
\mathbf w(f)=(1-b)\mathbf W_j+b\mathbf W_{j+1}.
\tag{C08}
$$

The nine wet-area tables $\mathbf W_0,\ldots,\mathbf W_8$ are exported by the JavaScript geometry. They are shared data, not independent predictions of liquid flow.

$$
k_i=k_s(1-\beta_i)+k_l\beta_i,\qquad
k_{h,ij}=\frac{2k_ik_j}{k_i+k_j},\qquad
q_{j\to i}=B_{p,i}\,k_{h,ij}(T_j-T_i).
\tag{C09}
$$

$B_{p,i}$ is the exported spherical face geometry factor `radialBase[pop]`. Each face flux is added to one radial shell and subtracted from its neighbor. Harmonic interface conductivity and Fourier conduction underlie the calculation; this file consumes the geometric factor rather than deriving it again.

$$
q_{{\rm exchange},i}=\dot m_{\rm exchange}\,w_i(h_{{\rm near},i}-h_{{\rm core},i}),\quad
\dot E_{{\rm near},i}\mathrel{-}=q_{{\rm exchange},i},\quad
\dot E_{{\rm core},i}\mathrel{+}=q_{{\rm exchange},i}.
\tag{C10}
$$

This is a conservative two-population exchange closure. $\dot m_{\rm exchange}$ and radial weights are shared exported inputs, not a solved mixing velocity field.

## 5. Effective bed conductance — project closure

**Code:** [line 41](../rotary_melter/Calculation.py#L41). These series/parallel/contact interpolations describe the implemented approximate bed. They are not claimed to be a fitted universal wax correlation.

$$
k_{s,c}=\frac{k_s}{1+R_c k_s/d_p},\quad
\phi=\phi_0+(1-\phi_0)f,\quad
k_1=k_{s,c}(1-f)+k_lf,\quad k_0=k_g(1-f)+k_lf.
\tag{C11}
$$

$$
k_{\rm series}=\left(\frac{\phi}{k_1}+\frac{1-\phi}{k_0}\right)^{-1},\quad
k_{\rm parallel}=\phi k_1+(1-\phi)k_0,\quad
k_{\rm bed}=k_{\rm series}+\chi(k_{\rm parallel}-k_{\rm series}).
\tag{C12}
$$

$$
V_{\rm bed}=m\left[\frac{1-f}{\rho_s\phi_0}+\frac f{\rho_l}\right],\qquad
G_{\rm bed}=\frac{k_{\rm bed}V_{\rm bed}^{2/3}}{\max(d_p,\lambda D_t)}.
\tag{C13}
$$

$R_c$ is `contactR`, $\chi$ is `contactTopology`, $\lambda$ is `bedPathFactor`, $d_p=\texttt{particle}/1000$ m and $D_t=\texttt{diameter}/1000$ m. $R_c$ has the area-specific resistance dimensions required to make $R_ck_s/d_p$ dimensionless. The characteristic area $V^{2/3}$ and path-length choice are project closures. Literature about rotary beds supports considering contact and gas pathways, but does not validate these exact interpolation coefficients; see the preserved [research notes](history/Research_Notes_v17.md).

## 6. Granule surface, film coupling and boundary solve

**Code:** [lines 42–43](../rotary_melter/Calculation.py#L42). **Derived half-shell and two-node energy balance.**

$$
r_p=\frac{d_p}{2},\quad\Delta r=\frac{r_p}{K},\quad
n_p=\frac{m_p}{\rho_s(4\pi r_p^3/3)},\quad
g_{s,p}=n_p\frac{4\pi r_p^2k_{{\rm outer},p}}{\Delta r/2},\quad
g_{{\rm film},j}=G_{p,j}w_j(f).
\tag{C14}
$$

The population index $p$ is near/core. Population masses and granule diameter determine a representative number of spheres; the reference solver does not track each sphere's thermal state separately.

$$
\begin{bmatrix}
g_{s,n}+\sum_jg_{{\rm film},j}+G_{\rm bed}&-G_{\rm bed}\\
-G_{\rm bed}&g_{s,c}+G_{\rm bed}
\end{bmatrix}
\begin{bmatrix}T_{b,n}\\T_{b,c}\end{bmatrix}
=\begin{bmatrix}
g_{s,n}T_{{\rm outer},n}+\sum_jg_{{\rm film},j}T_{i,j}\\
g_{s,c}T_{{\rm outer},c}
\end{bmatrix}.
\tag{C15}
$$

$$
q_{{\rm film},j}=g_{{\rm film},j}(T_{i,j}-T_{b,n}),\qquad
q_b=G_{\rm bed}(T_{b,n}-T_{b,c}).
\tag{C16}
$$

The film flux leaves the inner metal and enters the near outer shell. $q_b$ leaves that shell and enters the core outer shell. The boundary temperatures are massless algebraic interface nodes. This is not a resolved liquid convection boundary layer.

## 7. Water source and transient energy balance

**Code:** [lines 44–46 and 52–53](../rotary_melter/Calculation.py#L44). **Derived heat-capacity-flow relation**, with explicit source policy.

$$
F=\rho_wc_wQ_v,\quad q_{\rm requested}=\max[0,F(T_{\rm set}-T_{\rm return})],\quad
q_{\rm in}=\begin{cases}q_{\rm requested},&\texttt{sourceMode}=1,\\
\min(q_{\rm requested},1000P_{\rm boiler,kW}\eta),&\texttt{sourceMode}=0.
\end{cases}
\tag{C17}
$$

$$
T_{\rm in}=T_{\rm return}+q_{\rm in}/F,\qquad
F(T_{\rm in}-T_{\rm out})=q_{\rm water\to metal}+q_{\rm extra}+\frac{dE_w}{dt}.
\tag{C18}
$$

The source adds heat to the first water row of the circulating matrix. It does not actively cool water hotter than the setpoint. The transient storage term explains why initial 110/25 °C inlet/outlet temperatures can coexist with initially zero water-to-metal heat transfer. The earlier audit and its limits remain in [Startup_Audit_v22.md](history/Startup_Audit_v22.md).

## 8. Exterior insulation, convection, radiation and extra leakage

**Code:** [lines 47–53](../rotary_melter/Calculation.py#L47). **Basis:** Fourier resistance and Newton cooling [R2](https://web.mit.edu/16.unified/www/SPRING/propulsion/notes/node123.html); radiation constant [R3](https://industrialresources.ornl.gov/measur/suite/docs/group__physics__constants). The insulation uses the project's planar area approximation.

$$
G_{\rm ins}=\frac{k_{\rm ins}A_o}{\delta_{\rm ins}},\quad
q_{\rm conv}=h_eA_o(T_f-T_a),\quad
q_{\rm rad}=\epsilon\sigma A_o[(T_f+273.15)^4-(T_a+273.15)^4],\quad
\sigma=5.670374419\times10^{-8}.
\tag{C19}
$$

$$
G_{\rm ins}(T_o-T_f)=q_{\rm conv}+q_{\rm rad},\qquad
q_{{\rm extra},a}=(UA)_{\rm extra}\,w_a(T_{w,a}-T_a).
\tag{C20}
$$

With insulation, Python brackets $T_f$ between metal and ambient and bisects 28 times; without insulation $T_f=T_o$. The radiation surroundings are at ambient and view-factor/enclosure exchange is not solved. Extra leakage is distributed by exported axial weights and removed from the water rows. Exterior convection/radiation are removed from outer-metal rows. Positive values mean heat leaving the system.

## 9. ODEs, event, integration tolerances and Jacobian

**Code:** [lines 53–68](../rotary_melter/Calculation.py#L53). **Method reference:** [R4, SciPy `solve_ivp`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html), BDF/Radau and event semantics. This file delegates adaptive integration to SciPy.

$$
\dot h_i=\frac{\dot E_i}{m_i},\quad
\dot T_j=\frac{\dot E_j}{C_j},\quad
\frac{d}{dt}\begin{bmatrix}E_{\rm in}\\E_{\rm loss}\\E_{\rm conv}\\E_{\rm rad}\\E_{\rm extra}\end{bmatrix}
=\begin{bmatrix}q_{\rm in}\\\sum q_{\rm conv}+\sum q_{\rm rad}+\sum q_{\rm extra}\\\sum q_{\rm conv}\\\sum q_{\rm rad}\\\sum q_{\rm extra}\end{bmatrix}.
\tag{C21}
$$

$$
g(\mathbf y)=\min_iT(h_i)-T_{\rm target}=0,\quad
t_{\rm end}=3600\,\texttt{maxHours},\quad
\mathrm{rtol}=10^{-8},\quad
\mathrm{atol}=(10^{-4}\text{ for }h,\ 10^{-8}\text{ for }T,\ 10^{-3}\text{ for energies}).
\tag{C22}
$$

The event is terminal and detects increasing crossings. Dense interpolation is requested. A failed SciPy integration raises `RuntimeError`. The tolerances are project numerical settings, not physical accuracy guarantees. BLAS threads are limited to one for the solve.

$$
s_j=\begin{cases}1000,&j<B,\\1,&j\geq B,\end{cases}\quad
\delta_j=\sqrt{\varepsilon_{\rm machine}}\max(|y_j|,s_j),\quad
J_{:,j}=\frac{\mathbf f(\mathbf y+\delta_j\mathbf e_j)-\mathbf f(\mathbf y)}{(y_j+\delta_j)-y_j}\quad(j<D).
\tag{C23}
$$

The actual represented increment is used in the denominator. The last five Jacobian columns remain exactly zero because accumulated energies do not feed back into the ODE. The dense finite-difference array is returned as a CSR sparse matrix. This Jacobian is recomputed by the solver callback; its construction is independent of the production explicit RK2 integrator.

## 10. Stored energy, conservation and comparison criteria

**Code:** [lines 70–71](../rotary_melter/Calculation.py#L70), [`compare`, lines 82–97](../rotary_melter/Calculation.py#L82). **Derived diagnostics**, not literature correlations.

$$
\Delta E_{\rm stored}=\sum_i m_i(h_i-h_i^0)+\sum_jC_j(T_j-T_j^0),\quad
R_E=E_{\rm in}-E_{\rm loss}-\Delta E_{\rm stored},\quad
\varepsilon_E=\frac{|R_E|}{\max(1\ \mathrm J,|E_{\rm in}|)}.
\tag{C24}
$$

$$
\delta_t=\frac{|t_{\rm ref}-t_{\rm JS}|}{t_{\rm ref}},\quad
\delta_{E}=\frac{|E_{\rm in,ref}-E_{\rm in,JS}|}{E_{\rm in,ref}},\quad
\Delta T_{\rm out}=T_{\rm out,ref}-T_{\rm out,JS}.
\tag{C25}
$$

`compare()` runs both BDF and Radau. Its `passed` flag requires $\delta_t<0.005$ and $\delta_E<0.005$ for both and the hydraulic discrepancy below $10^{-8}$. The reported water-outlet difference and geometry discrepancies do **not** enter that final Boolean. No extra claim of experimental validity follows from the flag.

Reported near/core centers are shell indices 0 and $K$; target hours are seconds/3600. Joules are divided by $3.6\times10^6$ to obtain kWh. `wallSeconds` is a performance-counter difference; `nfev`, `njev` and `nlu` are SciPy work counters, not physical quantities.

## 11. Independent vessel quadrature

**Code:** [`geometry_check`, lines 73–80](../rotary_melter/Calculation.py#L73). **Derived spherical-cap geometry and numerical quadrature.**

$$
R=\frac{D_{t,\rm mm}}{2000},\quad L=\frac{L_{\rm mm}}{1000},\quad H_c=\frac{H_{c,\rm mm}}{1000},\quad
R_s=\frac{R^2+H_c^2}{2H_c}.
\tag{C26}
$$

$$
r(z)=\begin{cases}R,&0\leq z\leq L,\\
\sqrt{\max[0,R_s^2-(z-(R_s-H_c))^2]},&-H_c\leq z\leq0,\\
\sqrt{\max[0,R_s^2-((L-z)-(R_s-H_c))^2]},&L\leq z\leq L+H_c,
\end{cases}
\tag{C27}
$$

$$
V=\sum_{\rm segments}\int\pi r(z)^2\,dz,\qquad
A_s=\int_{\rm cylinder}2\pi R\,dz+\sum_{\rm heads}\int2\pi R_s\,dz.
\tag{C28}
$$

Segments are cylinder plus zero/one/two heads according to `heads`; quadrature uses `epsabs=1e-12`. $R_s$ is computed unconditionally, so this checker assumes positive head depth even if no head segment is requested. `st` and `ct` are computed from inclination but unused here: total volume and area are rotation invariant. Reported relative discrepancies divide absolute difference from exported geometry by the quadrature value.

## 12. Independent hydraulic equations

**Code:** [lines 87–96](../rotary_melter/Calculation.py#L87). **Basis:** Darcy–Weisbach and Colebrook [R5](https://doi.org/10.1680/ijoti.1939.13150); annular laminar expression is the derived concentric-annulus Poiseuille result. Transition interpolation is a project choice.

$$
A_f=\frac{\pi(D^2-d^2)}4,\quad D_h=D-d,\quad
u=\frac{Q_v}{A_f},\quad \mathrm{Re}=\frac{\rho_wuD_h}{\mu_w},\quad a=\frac dD,\quad Q_v=\frac{Q_{v,\mathrm{m^3/h}}}{3600}.
\tag{C29}
$$

$$
\mathrm{Po}=\begin{cases}64,&a=0,\\
\dfrac{64(1-a)^2(1-a^2)}{1-a^4-(1-a^2)^2/\ln(1/a)},&a>0,\end{cases}\qquad
f_{\rm lam}=\frac{\mathrm{Po}}{\mathrm{Re}}.
\tag{C30}
$$

$$
\frac1{\sqrt{f_t}}+2\log_{10}\left(\frac{\epsilon_r}{3.7D_h}+\frac{2.51}{\mathrm{Re}\sqrt{f_t}}\right)=0,\quad
f_D=\begin{cases}f_{\rm lam},&\mathrm{Re}<2300,\\
f_{\rm lam}+(f_t-f_{\rm lam})\dfrac{\mathrm{Re}-2300}{1700},&2300\leq\mathrm{Re}<4000,\\f_t,&\mathrm{Re}\geq4000.\end{cases}
\tag{C31}
$$

`brentq` solves within $[0.0001,0.5]$ with `xtol=1e-14`; roughness is converted from mm to m. This is a **Darcy**, not Fanning, friction factor.

$$
\Delta p_k=\left(f_D\frac{L_k}{D_{h,k}}+K_k\right)\frac{\rho_wu_k^2}{2},\quad
\Delta p_{\rm total}=\sum_k\Delta p_k+10^5(p_{\rm joint,bar}+p_{\rm equipment,bar}),\quad
\delta_p=\frac{|\Delta p_{\rm total}-\Delta p_{\rm JS}|}{\max(1\ \mathrm{Pa},|\Delta p_{\rm total}|)}.
\tag{C32}
$$

The five segments are supply pipe, feed shaft, jacket annulus, shaft-return annulus and return pipe. Diameters are converted from mm; prescribed pipe lengths are already in meters except the vessel length used for the jacket. Total bar is total Pa/$10^5$. Applying the turbulent pipe correlation through hydraulic diameter to annuli is a modeling approximation, not proof that arbitrary passage geometries follow the circular-pipe law. The code compares specified-flow pressure loss; it does not solve a pump curve or determine available flow automatically.

## 13. Additional production JavaScript formulas

These equations support the production model but are not duplicated in Python `Calculation.py`.

### 13.1 Saturation pressure

**Code:** [`Calculation.js`, `psat`, line 25](../rotary_melter/web/calculations/Calculation.js#L25). **Source:** [R6, IAPWS SR1-86(1992), equation (1)](https://iapws.org/technical-guidance/release/Supp-sat).

$$
\tau=1-\frac{T+273.15}{647.096},\qquad
p_{\rm sat}=220.64\exp\left[\frac{647.096}{T+273.15}\sum_{i=1}^6a_i\tau^{b_i}\right]\ [\mathrm{bar}],
\tag{C33}
$$

with $\mathbf a=(-7.85951783,1.84408259,-11.7866497,22.6807411,-15.9618719,1.80122502)$ and $\mathbf b=(1,1.5,3,3.5,4,7.5)$. Use the correlation within the IAPWS saturation region. The existing input guard is rounded to $0<T_{\rm in}<374$ °C, slightly above the exact critical temperature of 373.946 °C at its upper end; it is not a complete correlation-domain check. The code does not simulate boiling.

### 13.2 RPM sensitivity and rotation

**Code:** [`Calculation.js`, `rpmHeatTransfer` / `rotation`, lines 22–23](../rotary_melter/web/calculations/Calculation.js#L22). Rotation measures are derived; the heat-transfer sensitivity is explicitly a **project phenomenological law**.

$$
h_{\rm rpm}=\begin{cases}
h_{\rm ref}[1+g(N/N_{\rm ref})^p],&\texttt{rpmMode}=0,\\
\min[h_{\rm limit},h_0+(h_{\rm ref}-h_0)(N/N_{\rm ref})^p],&\texttt{rpmMode}=1,
\end{cases}
\tag{C34}
$$

$$
\omega=\frac{2\pi N_{\rm rpm}}{60},\quad u_w=\omega R,\quad
\mathrm{Fr}=\frac{\omega^2R}{g},\quad
\mathrm{Fr}_n=\frac{\omega^2R}{g\cos\theta},\quad
N_{\rm balance}=\frac{60}{2\pi}\sqrt{\frac{g\cos\theta}{R}}.
\tag{C35}
$$

The last two values are unavailable when $g\cos\theta\leq10^{-6}$; $g=9.80665$ m/s² in this JavaScript diagnostic. Native mechanics uses its own documented $9.81$ m/s² constant. The balance RPM is a force-scale indicator, not an established optimal melting speed. Rotating-cylinder regimes depend on additional properties; see [R7, Mellmann (2001)](https://doi.org/10.1016/S0032-5910(00)00402-2). That paper does not validate C34 for melting wax.

### 13.3 Explicit production integration and conditional GCI

The production thermal modules use explicit midpoint RK2 with stable time-step selection; Python uses BDF/Radau:

$$
\mathbf k_1=\mathbf f(\mathbf y_n),\quad
\mathbf y_{1/2}=\mathbf y_n+\frac{\Delta t}{2}\mathbf k_1,\quad
\mathbf y_{n+1}=\mathbf y_n+\Delta t\,\mathbf f(\mathbf y_{1/2}).
\tag{C36}
$$

**Code:** [production particle thermal model](../rotary_melter/web/calculations/ParticleHeatTransfer.js), integration loop; [GCI, `Convergence.js`, lines 5–12](../rotary_melter/web/calculations/Convergence.js#L5). **GCI source:** [R8, NASA NPARC grid-convergence tutorial](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html).

$$
p=\frac{\ln|(f_c-f_m)/(f_m-f_f)|}{\ln r},\quad
f_\infty=f_f+\frac{f_f-f_m}{r^p-1},\quad
\mathrm{GCI}_f=\frac{1.25|(f_m-f_f)/f_f|}{r^p-1},\quad
\mathrm{GCI}_m=\frac{1.25|(f_c-f_m)/f_m|}{r^p-1}.
\tag{C37}
$$

The reported asymptotic ratio is $\mathrm{GCI}_m/(r^p\mathrm{GCI}_f)$. Values are unavailable for invalid/nonfinite inputs, nonpositive refinement ratio increment, zero fine result, differences below the supplied noise floor, nonmonotonic differences or nonpositive observed order. The factor 1.25 is the three-grid safety factor; the estimate is conditional, not proof of physical validity or asymptotic convergence.

## 14. Coverage, source provenance and references

| Python definition | Lines | Equation coverage |
| --- | --- | --- |
| `enthalpy`, `temperature` | [11–16](../rotary_melter/Calculation.py#L11) | C01–C02 |
| `solve`, nested `link` / `rhs` / `target` / `jacobian` | [18–71](../rotary_melter/Calculation.py#L18) | C03–C25 |
| `geometry_check`, nested `radius` and quadrature lambdas | [73–80](../rotary_melter/Calculation.py#L73) | C26–C28 |
| `compare`, including Colebrook lambda | [82–97](../rotary_melter/Calculation.py#L82) | C25, C29–C32 |
| CLI JSON load/save | [99–102](../rotary_melter/Calculation.py#L99) | No additional physical equations |

- Python source SHA-256: `c4a35ddfb46f938da5b2d070a7a01bbde07dfea391bba72476cf1d168ee3a149`.
- Coverage: **10 function definitions**, including nested helpers, plus **37 numbered equation groups**.
- The independent calculation algorithms were preserved during the V11 source reorganization.

Rendering was checked using KaTeX 0.16.22 with strict error reporting: **37 display groups and 48 inline expressions parsed without errors**. A generated HTML preview and `render_check.json` are kept under `outputs/equation_documentation/` and excluded from Git. Markdown Preview Enhanced 0.8.40 is installed; both its KaTeX renderer and VS Code's built-in math preview are enabled for this workspace. A separate TeX distribution is not needed for these Markdown formulas.


Local links use line fragments such as `#L18`. If the editor opens the file without jumping, use **Ctrl+G** and the printed line number. Function names and ranges are supplied as an additional lookup aid.

Literature/software references checked during this migration:

1. **R1 — Voller, Cross and Markatos (1987)**, “An enthalpy method for convection/diffusion phase change,” *IJNME*, 24, 271–284. [DOI](https://doi.org/10.1002/nme.1620240119). Method-family background; the exact piecewise constitutive parameters are project inputs.
2. **R2 — MIT Unified Engineering**, *Combined Conduction and Convection*, §17.2, equations 17.20–17.26. [Course notes](https://web.mit.edu/16.unified/www/SPRING/propulsion/notes/node123.html). Resistance/film physics; not a source for the project's bed-contact interpolation.
3. **R3 — Oak Ridge National Laboratory, MEASUR**, [SI physics constants](https://industrialresources.ornl.gov/measur/suite/docs/group__physics__constants). Supports the Stefan–Boltzmann constant used in C19.
4. **R4 — SciPy developers**, [`solve_ivp`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html), method and events documentation. The project delegates BDF/Radau integration to this API; its tolerances are code settings.
5. **R5 — Colebrook, C. F. (1939)**, “Turbulent flow in pipes, with particular reference to the transition region between the smooth and rough pipe laws,” *Journal of the Institution of Civil Engineers*, 11(4), 133–156. [DOI](https://doi.org/10.1680/ijoti.1939.13150), [publisher record](https://www.emerald.com/jince/article/11/4/133/417643). Supports the turbulent friction-law family; linear transition blending and user-entered local losses are separate choices. The publisher record was checked; unrestricted access to the complete historical paper was unavailable.
6. **R6 — IAPWS (1992)**, SR1-86(1992), *Revised Supplementary Release on Saturation Properties of Ordinary Water Substance*, equation (1). [Official release](https://iapws.org/technical-guidance/release/Supp-sat). Supports C33 coefficients and critical constants.
7. **R7 — Mellmann (2001)**, “The transverse motion of solids in rotating cylinders—forms of motion and transition behavior,” *Powder Technology*. [DOI](https://doi.org/10.1016/S0032-5910(00)00402-2). Context for rotating-bed regime dependence, not calibration of melting or RPM–film sensitivity.
8. **R8 — NASA NPARC Alliance**, *Examining Spatial (Grid) Convergence*. [Official tutorial](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html). Basis for observed order, Richardson extrapolation and conditional GCI in C37.
9. **R9 — Erin Catto (2024)**, [*Solver2D*](https://box2d.org/posts/2024/02/solver2d/). Background for the separately implemented native sequential-impulse/warm-start mechanics. The program does not execute Box2D. Mechanics equations and limits are discussed in [Motion_Research_v18.md](history/Motion_Research_v18.md) and [Verification_Motion_v18.md](history/Verification_Motion_v18.md).

No paper is asserted to establish the exact $R_c$, $\chi$, $\lambda$, RPM sensitivity, occupancy interpolation, population exchange, solver tolerance or acceptance-threshold choices in this project. Those are documented directly from the implementation.
