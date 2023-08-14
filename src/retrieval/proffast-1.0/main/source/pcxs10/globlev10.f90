!     Last change:  BLA   1 Jan 2017   10:41 pm
module globlev10

use globvar10, only: maxlev,maxams,maxavk,maxtau

implicit none

type levels
    sequence
    real(8),dimension(maxlev) :: T_K,p_Pa,h_m
    real(8),dimension(maxlev) :: n_cbm,n_cbm_dry,colair,colair_do,colair_up
    real(8),dimension(maxlev,maxams) :: sza_rad
    real(8),dimension(maxlev,maxavk) :: sza_rad_avk
    real(8),dimension(maxlev,maxtau) :: vmr_ppmv
    real(8),dimension(maxlev,maxavk,maxtau) :: colsens
end type

type (levels) :: lev

end module globlev10
