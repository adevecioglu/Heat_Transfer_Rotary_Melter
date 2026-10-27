// Independent field post-processing in double precision; no dependent time step
// or shared-particle constraint is reordered by this GPU analysis.
extern "C" __global__ void exterior_flux(const double* temperature,const double* area,
    double ambient,double convection,double emissivity,int cells,int count,
    double* convective,double* radiative) {
    const int i=blockDim.x*blockIdx.x+threadIdx.x;
    if(i>=count)return;
    const double tk=temperature[i]+273.15,ak=ambient+273.15;
    const double a=area[i%cells];
    convective[i]=convection*a*(temperature[i]-ambient);
    radiative[i]=emissivity*5.670374419e-8*a*(tk*tk*tk*tk-ak*ak*ak*ak);
}
